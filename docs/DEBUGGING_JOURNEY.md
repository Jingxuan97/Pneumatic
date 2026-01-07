# Debugging Journey - Comprehensive Bug Fixes

This document details all the bugs encountered during development, the debugging process, and the solutions implemented. It serves as a reference for understanding complex issues and their resolutions.

---

## Table of Contents

1. [Critical Production Bugs](#critical-production-bugs)
   - [Timezone Mismatch with PostgreSQL](#1-timezone-mismatch-with-postgresql)
   - [AsyncIO Event Loop Error](#2-asyncio-event-loop-error)
   - [WebSocket Connection Closing After Messages](#3-websocket-connection-closing-after-messages)
   - [Real-Time Message Display Issues](#4-real-time-message-display-issues)

2. [Frontend Bugs](#frontend-bugs)
   - [crypto.randomUUID() Browser Compatibility](#5-cryptorandomuuid-browser-compatibility)
   - [Duplicate Event Listeners](#6-duplicate-event-listeners)
   - [Send Button Not Working](#7-send-button-not-working)

3. [AWS Deployment Issues](#aws-deployment-issues)
   - [502 Bad Gateway Errors](#8-502-bad-gateway-errors)
   - [RDS Security Group Configuration](#9-rds-security-group-configuration)
   - [Database Connection Issues](#10-database-connection-issues)

4. [Authentication & Authorization](#authentication--authorization)
   - [WebSocket Authentication Failures](#11-websocket-authentication-failures)
   - [Token Validation Issues](#12-token-validation-issues)

5. [Data Persistence](#data-persistence)
   - [Database Reset on Every Run](#13-database-reset-on-every-run)
   - [Duplicate Conversations](#14-duplicate-conversations)

---

## Critical Production Bugs

### 1. Timezone Mismatch with PostgreSQL

**Severity:** 🔴 Critical - Blocked all message sending in production

**Symptoms:**
```
Error: (sqlalchemy.dialects.postgresql.asyncpg.Error)
<class 'asyncpg.exceptions.DataError'>: invalid input for query argument $6:
datetime.datetime(2026, 1, 6, 23, 55, 59...
(can't subtract offset-naive and offset-aware datetimes)

[SQL: INSERT INTO messages (id, message_id, sender_id, conversation_id, content, created_at)
VALUES (%s, %s, %s, %s, %s, %s)]
[parameters: (..., datetime.datetime(2026, 1, 6, 23, 55, 59, 174477, tzinfo=datetime.timezone.utc))]
```

**Root Cause:**
- The database column was defined as `DateTime(timezone=False)` (expects naive datetime)
- The code was using `datetime.now(timezone.utc)` (timezone-aware datetime)
- PostgreSQL's `TIMESTAMP WITHOUT TIME ZONE` cannot accept timezone-aware datetimes
- This worked in SQLite (more lenient) but failed in PostgreSQL (strict)

**Debugging Process:**
1. **Initial Investigation**: Error appeared only in production (PostgreSQL), not locally (SQLite)
2. **Error Analysis**: The error message clearly indicated timezone mismatch
3. **Code Review**: Found mismatch between model definition and usage:
   - `app/models.py`: `created_at = sa.Column(sa.DateTime(timezone=False), ...)`
   - `app/store_sql.py`: `created_at=datetime.now(timezone.utc)` (timezone-aware)
4. **Model Default Function**: Also found `utc_now()` returning timezone-aware datetime

**Solution:**
```python
# app/models.py - Fixed default function
def utc_now():
    # Return naive datetime to match column definition (timezone=False)
    return datetime.now(timezone.utc).replace(tzinfo=None)

# app/store_sql.py - Fixed explicit datetime creation
now_utc = datetime.now(timezone.utc)
created_at_naive = now_utc.replace(tzinfo=None) if now_utc.tzinfo else now_utc

msg = Message(
    ...
    created_at=created_at_naive
)
```

**Key Learnings:**
- Always match database column timezone settings with Python datetime objects
- Test with production database type (PostgreSQL) during development
- SQLite is more lenient - don't rely on it for timezone validation

**Files Changed:**
- `app/models.py` - Fixed `utc_now()` function
- `app/store_sql.py` - Fixed `save_message()` datetime handling

---

### 2. AsyncIO Event Loop Error

**Severity:** 🔴 Critical - Crashed application on startup in production

**Symptoms:**
```
RuntimeError: There is no current event loop in thread 'MainThread'.
```

**Root Cause:**
- `asyncio.Lock()` was being created at module import time (in `__init__` methods)
- At import time, no asyncio event loop exists yet
- The event loop is created later when FastAPI starts
- This caused a race condition where locks were created before the event loop

**Debugging Process:**
1. **Initial Error**: Application crashed immediately on startup
2. **Stack Trace Analysis**: Error occurred in `app/websockets.py` and `app/rate_limit.py`
3. **Code Inspection**: Found `asyncio.Lock()` being created in `__init__`:
   ```python
   class ConnectionManager:
       def __init__(self):
           self._lock = asyncio.Lock()  # ❌ Created at import time
   ```
4. **Understanding AsyncIO**: Researched that `asyncio.Lock()` requires an active event loop
5. **Testing**: Confirmed error only occurred in production (different import order)

**Solution - Lazy Initialization:**
```python
# app/websockets.py
class ConnectionManager:
    def __init__(self):
        self.active: Dict[str, List[WebSocket]] = {}
        self._lock = None  # ✅ Initialize as None

    def _get_lock(self):
        """Lazy initialization - creates lock when first needed in async context."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def connect(self, user_id: str, websocket: WebSocket):
        async with self._get_lock():  # ✅ Lock created here (event loop exists)
            ...
```

**Applied to:**
- `app/websockets.py` - `ConnectionManager._lock`
- `app/rate_limit.py` - `RateLimiter._lock`

**Key Learnings:**
- Never create asyncio primitives at module/class import time
- Use lazy initialization for asyncio objects
- Test import order can differ between dev and production

**Files Changed:**
- `app/websockets.py`
- `app/rate_limit.py`
- `docs/TROUBLESHOOTING.md` - Documented the bug

---

### 3. WebSocket Connection Closing After Messages

**Severity:** 🟡 High - Prevented real-time messaging

**Symptoms:**
- Messages were sent successfully
- WebSocket connection closed immediately after (code 1000 - normal closure)
- Messages were not received by other users
- Connection would reconnect, but messages were lost

**Debugging Process:**
1. **Initial Observation**: Console showed "Message sent successfully" but no broadcast received
2. **WebSocket State Monitoring**: Added logging to track connection state
3. **Error Investigation**: Checked backend logs for exceptions
4. **Code Review**: Found that unhandled exceptions in message processing would close the connection:
   ```python
   except Exception as e:
       await manager.disconnect(user_id, websocket)
       raise  # ❌ This closed the connection
   ```
5. **Exception Analysis**: Discovered the timezone error (Bug #1) was causing exceptions
6. **Connection Lifecycle**: Realized exceptions were closing connections before broadcast

**Solution:**
```python
# app/main.py - Improved error handling
elif typ == "message":
    try:
        # ... message processing ...
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        await websocket.send_json({"type": "error", "reason": str(e)})
        continue  # ✅ Continue loop, don't close connection

except Exception as e:
    # Log but don't re-raise - keep connection alive
    logger.error(f"WebSocket error: {e}", exc_info=True)
    try:
        await websocket.send_json({"type": "error", "reason": f"server error: {str(e)}"})
    except Exception:
        pass
    await manager.disconnect(user_id, websocket)
    return  # ✅ Clean disconnect, don't re-raise
```

**Key Learnings:**
- Always handle exceptions gracefully in WebSocket handlers
- Don't re-raise exceptions that should be handled
- Log errors before disconnecting
- Send error messages to client before closing

**Files Changed:**
- `app/main.py` - Comprehensive error handling in WebSocket endpoint

---

### 4. Real-Time Message Display Issues

**Severity:** 🟡 High - Core functionality broken

**Symptoms:**
- Messages sent by User A were not appearing for User B in real-time
- Messages only appeared after page refresh
- Console showed messages were being received via WebSocket
- But messages were not being displayed in the UI

**Debugging Process:**
1. **Initial Testing**: Two users in same conversation, messages not appearing
2. **WebSocket Logging**: Added extensive logging to `ws.onmessage` handler
3. **Message Reception**: Confirmed messages were being received (console logs)
4. **DOM Inspection**: Checked if messages were being added to DOM
5. **Code Flow Analysis**: Traced the message handling flow:
   - Message received ✅
   - Parsed correctly ✅
   - Conversation ID matched ✅
   - But not displayed ❌
6. **Container Check**: Found `messagesContainer` might be getting cleared
7. **Duplicate Prevention**: Discovered messages might be added multiple times
8. **Empty State Handling**: Found `innerHTML = ''` was clearing all messages

**Solution:**
```javascript
// static/chat.html - Improved message handling
ws.onmessage = async (event) => {
    if (data.type === 'message') {
        const msg = data.message;
        const convId = msg.conversation_id;

        // Check if this is the currently selected conversation
        if (convId === currentConversationId) {
            const container = document.getElementById('messagesContainer');

            // Remove empty state without clearing all messages
            const emptyState = container.querySelector('.empty-state');
            if (emptyState) {
                emptyState.remove();  // ✅ Remove only empty state
            }

            // Check for duplicates using message_id
            const existingMessage = container.querySelector(
                `[data-message-id="${msg.message_id}"]`
            );
            if (existingMessage) {
                return;  // ✅ Skip duplicate
            }

            // Create and append message
            const messageDiv = document.createElement('div');
            messageDiv.setAttribute('data-message-id', msg.message_id);
            container.appendChild(messageDiv);
        }
    }
};
```

**Additional Fixes:**
- Updated `displayMessages()` to preserve existing messages
- Added `data-message-id` attributes for duplicate tracking
- Improved empty state handling

**Key Learnings:**
- Always check for duplicates when adding dynamic content
- Use data attributes for tracking (not just IDs)
- Be careful with `innerHTML` - it clears everything
- Prefer `remove()` and `appendChild()` over `innerHTML`

**Files Changed:**
- `static/chat.html` - Message display logic
- `static/chat.html` - `displayMessages()` function

---

## Frontend Bugs

### 5. crypto.randomUUID() Browser Compatibility

**Severity:** 🟡 Medium - Broke message sending in some browsers

**Symptoms:**
```
Uncaught TypeError: crypto.randomUUID is not a function
    at sendMessage (chat.html:928:38)
```

**Root Cause:**
- `crypto.randomUUID()` is a relatively new Web API
- Not available in all browsers (especially older versions)
- Not available in some browser contexts

**Debugging Process:**
1. **Error Report**: User reported send button not working
2. **Console Check**: Found `crypto.randomUUID is not a function` error
3. **Browser Compatibility**: Checked MDN - `crypto.randomUUID()` requires modern browsers
4. **Fallback Needed**: Required a cross-browser UUID generator

**Solution:**
```javascript
// static/chat.html - Cross-browser UUID generator
function generateUUID() {
    // Use native API if available
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        return crypto.randomUUID();
    }
    // Fallback UUID v4 generator
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Usage
const messageId = generateUUID();  // ✅ Works in all browsers
```

**Key Learnings:**
- Always check browser compatibility for new Web APIs
- Provide fallbacks for critical functionality
- Test in multiple browsers

**Files Changed:**
- `static/chat.html` - Added `generateUUID()` function

---

### 6. Duplicate Event Listeners

**Severity:** 🟢 Low - Annoying console warnings

**Symptoms:**
```
Cannot send empty message
sendMessage @ chat.html:1027
(anonymous) @ chat.html:1109
```

**Root Cause:**
- Button had both `onclick="sendMessage()"` attribute
- AND an event listener attached via `addEventListener`
- Both fired on click, causing duplicate execution
- First execution cleared input, second execution tried to send empty message

**Debugging Process:**
1. **Warning Observation**: Console showed "Cannot send empty message" after successful send
2. **Event Flow**: Traced execution - message sent, input cleared, then warning
3. **Code Review**: Found duplicate handlers:
   ```html
   <button onclick="sendMessage()">Send</button>
   ```
   ```javascript
   sendBtn.addEventListener('click', sendMessage);  // ❌ Duplicate
   ```
4. **Timing**: Event listener fired after onclick, but input was already cleared

**Solution:**
```javascript
// static/chat.html - Removed duplicate event listener
// Keep only onclick attribute, remove addEventListener
// The onclick handler is sufficient and simpler
```

**Key Learnings:**
- Don't mix inline handlers and event listeners
- Choose one approach and stick with it
- Simpler is better - onclick is fine for simple cases

**Files Changed:**
- `static/chat.html` - Removed duplicate event listener

---

### 7. Send Button Not Working

**Severity:** 🟡 Medium - Core functionality broken

**Symptoms:**
- Send button appeared to do nothing
- No console errors initially
- Messages not being sent

**Debugging Process:**
1. **User Report**: "Send button doesn't work"
2. **Initial Check**: No obvious errors in console
3. **Added Logging**: Added extensive logging to `sendMessage()`:
   ```javascript
   console.log('sendMessage() called');
   console.log('Current state:', {
       currentConversationId,
       wsExists: !!ws,
       wsState: ws ? ws.readyState : 'N/A'
   });
   ```
4. **State Investigation**: Discovered various potential issues:
   - WebSocket not connected
   - No conversation selected
   - Input validation failing
5. **Progressive Debugging**: Added checks for each condition
6. **Root Cause**: Multiple potential issues, needed comprehensive validation

**Solution:**
```javascript
function sendMessage() {
    // Comprehensive validation with clear error messages
    if (!content) {
        console.warn('Cannot send empty message');
        return;
    }

    if (!currentConversationId) {
        alert('Please select a conversation first');
        return;
    }

    if (!ws || ws.readyState !== WebSocket.OPEN) {
        alert('Not connected. Attempting to reconnect...');
        connectWebSocket();
        return;
    }

    // Send message...
}
```

**Key Learnings:**
- Add comprehensive logging for debugging
- Validate all preconditions
- Provide clear error messages to users
- Handle edge cases (no connection, no conversation, etc.)

**Files Changed:**
- `static/chat.html` - Enhanced `sendMessage()` with validation and logging

---

## AWS Deployment Issues

### 8. 502 Bad Gateway Errors

**Severity:** 🔴 Critical - Application completely unavailable

**Symptoms:**
- Health check showing "Red" status
- All requests returning 502 Bad Gateway
- Application not starting

**Debugging Process:**
1. **Initial Deployment**: `eb create` succeeded but health check failed
2. **Log Analysis**: `eb logs` showed various errors:
   - Missing `SECRET_KEY`
   - Database connection failures
   - Module import errors
3. **Environment Variables**: Checked `eb printenv` - variables missing
4. **Step-by-Step Debugging**:
   - Set `SECRET_KEY` (32+ characters)
   - Set `DATABASE_URL` (correct format)
   - Verified RDS security group
   - Checked region matching
5. **Multiple Iterations**: Required several deploy cycles to identify all issues

**Solutions:**
```bash
# Set required environment variables
eb setenv SECRET_KEY="your-32-character-secret-key" \
         DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db" \
         ALLOWED_ORIGINS="*"

# Wait for deployment
eb deploy

# Check logs
eb logs | tail -100

# Test endpoints
curl http://your-env.elasticbeanstalk.com/health
curl http://your-env.elasticbeanstalk.com/ready
```

**Key Learnings:**
- Always set environment variables before first deployment
- Check logs immediately after deployment
- Test health endpoints systematically
- Document required environment variables

**Documentation Created:**
- `docs/TROUBLESHOOTING.md` - Comprehensive troubleshooting guide
- `docs/EB_DEPLOYMENT.md` - Step-by-step deployment guide

---

### 9. RDS Security Group Configuration

**Severity:** 🔴 Critical - Database completely inaccessible

**Symptoms:**
- `/ready` endpoint returning 503
- Database connection timeouts
- "Connection refused" errors in logs

**Debugging Process:**
1. **Connection Failure**: Application couldn't connect to RDS
2. **Security Group Check**: RDS security group didn't allow EB security group
3. **Finding EB Security Group**:
   - Get from EC2 console
   - Or from `eb status` output
4. **Configuration Steps**:
   - RDS Console → Database → Security Group
   - Edit Inbound Rules
   - Add PostgreSQL rule
   - Source: EB Security Group ID
5. **Verification**: Test connection after rule addition

**Solution:**
```
AWS Console → RDS → Your Database → Security Group
→ Inbound Rules → Edit
→ Add Rule:
   Type: PostgreSQL
   Source: [EB Security Group ID]
→ Save
```

**Key Learnings:**
- Security groups are critical for AWS networking
- EB and RDS must be in same region
- Security group rules take 1-2 minutes to propagate
- Always verify security group configuration

**Documentation Created:**
- `docs/AWS_DEPLOYMENT_GUIDE.md` - Detailed security group setup

---

### 10. Database Connection Issues

**Severity:** 🟡 High - Application functional but database errors

**Symptoms:**
- `InvalidCatalogNameError: database "pneumatic_admin" does not exist`
- Connection attempts failing
- Wrong database name in connection string

**Debugging Process:**
1. **Error Analysis**: Database name in URL didn't match actual database
2. **RDS Investigation**: Checked RDS console - database name was `postgres` (default)
3. **URL Format**: Connection string had username as database name
4. **Testing**: Created test script to try different database names
5. **Resolution**: Updated `DATABASE_URL` to use correct database name

**Solution:**
```python
# Correct DATABASE_URL format
DATABASE_URL = "postgresql+asyncpg://username:password@host:5432/postgres"
#                                                                    ^^^^^^^^
#                                                              Actual DB name
```

**Key Learnings:**
- RDS default database is usually `postgres`
- Database name in URL must match actual database
- Test database connection before deploying
- Username ≠ database name

**Files Changed:**
- Environment variable `DATABASE_URL` in Elastic Beanstalk

---

## Authentication & Authorization

### 11. WebSocket Authentication Failures

**Severity:** 🟡 Medium - Users disconnected unexpectedly

**Symptoms:**
- WebSocket connections closing with code 1008 (Policy violation)
- Users redirected to login page
- "User not found" errors

**Root Cause:**
- Database was reset in development, invalidating existing tokens
- Tokens stored in localStorage became invalid
- Frontend didn't validate tokens on page load

**Debugging Process:**
1. **User Reports**: "I was logged in but got kicked out"
2. **Error Analysis**: WebSocket close code 1008 = authentication failure
3. **Token Validation**: Tokens were valid format but user didn't exist
4. **Database Reset**: Realized dev database was being reset
5. **Frontend Fix**: Added token validation on page load

**Solution:**
```javascript
// static/index.html - Validate token on page load
window.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('accessToken');
    if (token) {
        try {
            const response = await fetch(`${API_BASE}/auth/me`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) {
                // Token invalid, clear storage
                localStorage.clear();
            }
        } catch (error) {
            localStorage.clear();
        }
    }
});
```

**Key Learnings:**
- Always validate tokens on frontend
- Handle token expiration gracefully
- Clear invalid tokens from storage
- Provide clear error messages

**Files Changed:**
- `static/index.html` - Token validation on load
- `static/chat.html` - Auth error handling

---

### 12. Token Validation Issues

**Severity:** 🟢 Low - Minor UX issues

**Symptoms:**
- Users seeing "logged in as Bob" when not actually logged in
- Stale login information displayed

**Root Cause:**
- Frontend displayed login status from localStorage without validation
- Tokens could be invalid but still stored

**Solution:**
- Added token validation on page load
- Clear localStorage if token invalid
- Show accurate login status

**Files Changed:**
- `static/index.html` - Token validation

---

## Data Persistence

### 13. Database Reset on Every Run

**Severity:** 🟡 Medium - Data loss in development

**Symptoms:**
- All users and messages deleted on server restart
- Database file deleted on import

**Root Cause:**
- `app/db.py` had code that deleted `dev.db` on import
- This was for "clean" development but caused data loss

**Solution:**
```python
# app/db.py - Removed automatic deletion
# Changed from:
# if os.path.exists("dev.db"):
#     os.remove("dev.db")

# To:
# Only create tables if they don't exist - preserves existing data
if DATABASE_URL.startswith("sqlite"):
    Base.metadata.create_all(sync_engine)  # Creates if missing, doesn't drop
```

**Key Learnings:**
- Don't delete data automatically
- Use separate test databases for testing
- Preserve development data

**Files Changed:**
- `app/db.py` - Removed automatic database deletion

---

### 14. Duplicate Conversations

**Severity:** 🟢 Low - UX issue

**Symptoms:**
- Multiple 1-on-1 conversations between same two users
- Users could create duplicates by clicking multiple times

**Root Cause:**
- No check for existing 1-on-1 conversations
- Frontend didn't prevent multiple simultaneous requests

**Solution:**
```python
# app/routes.py - Check for existing 1-on-1
if len(member_ids) == 2:
    existing_conv = await store.find_one_on_one_conversation(
        member_ids[0], member_ids[1]
    )
    if existing_conv:
        return existing_conv  # Return existing instead of creating
```

```javascript
// static/chat.html - Prevent multiple clicks
let creatingConversation = false;

async function startConversationWithUser(...) {
    if (creatingConversation) return;  // Prevent duplicates
    creatingConversation = true;
    try {
        // ... create conversation ...
    } finally {
        creatingConversation = false;
    }
}
```

**Key Learnings:**
- Check for existing resources before creating
- Prevent duplicate requests from frontend
- Use flags to prevent race conditions

**Files Changed:**
- `app/routes.py` - Check for existing conversations
- `app/store_sql.py` - Added `find_one_on_one_conversation()`
- `static/chat.html` - Prevent duplicate requests

---

## Debugging Methodology

### General Approach

1. **Reproduce the Issue**
   - Understand when/where it occurs
   - Check if it's consistent or intermittent
   - Test in different environments

2. **Gather Information**
   - Check console logs (frontend)
   - Check application logs (backend)
   - Check error messages and stack traces
   - Check network requests (DevTools)

3. **Isolate the Problem**
   - Narrow down to specific component
   - Test in isolation if possible
   - Check related systems (database, WebSocket, etc.)

4. **Hypothesize and Test**
   - Form hypothesis about root cause
   - Test hypothesis with targeted changes
   - Verify fix doesn't break other things

5. **Document the Solution**
   - Update code comments
   - Update documentation
   - Add tests if applicable

### Tools Used

- **Browser DevTools**: Console, Network tab, Elements inspector
- **Backend Logging**: Structured JSON logs, error tracking
- **AWS Tools**: `eb logs`, `eb printenv`, AWS Console
- **Database Tools**: Connection testing, query inspection
- **Code Analysis**: Linters, type checkers, manual review

### Common Patterns

1. **Environment Differences**: Many bugs only appeared in production
   - Solution: Test with production-like environment
   - Use environment variables for configuration

2. **Async/Await Issues**: Race conditions, event loop problems
   - Solution: Proper async handling, lazy initialization
   - Use locks for shared state

3. **Type Mismatches**: Database types vs Python types
   - Solution: Match types exactly, test with production DB
   - Use type hints and validation

4. **State Management**: Frontend state getting out of sync
   - Solution: Single source of truth, proper state updates
   - Validate state before operations

---

## Lessons Learned

### Development Practices

1. **Test with Production Database**: SQLite is too lenient, use PostgreSQL
2. **Environment Parity**: Keep dev and prod environments similar
3. **Comprehensive Logging**: Log everything during debugging
4. **Error Handling**: Always handle errors gracefully
5. **Browser Compatibility**: Test in multiple browsers

### Code Quality

1. **Type Safety**: Use type hints and validation
2. **Error Messages**: Provide clear, actionable error messages
3. **Code Comments**: Document complex logic
4. **Code Review**: Review code for potential issues
5. **Testing**: Write tests for edge cases

### Deployment

1. **Environment Variables**: Set all required variables before deployment
2. **Security Groups**: Configure networking correctly
3. **Health Checks**: Monitor health endpoints
4. **Logs**: Check logs immediately after deployment
5. **Documentation**: Document deployment process

---

## Conclusion

This debugging journey involved fixing critical production bugs, frontend compatibility issues, AWS deployment problems, and various UX improvements. The key to successful debugging was:

1. **Systematic Approach**: Methodically investigating each issue
2. **Comprehensive Logging**: Adding detailed logs to understand flow
3. **Environment Testing**: Testing in production-like environments
4. **Documentation**: Documenting solutions for future reference
5. **Prevention**: Learning from bugs to prevent similar issues

Many of these bugs were discovered during production deployment, highlighting the importance of:
- Testing with production-like environments
- Comprehensive error handling
- Proper logging and monitoring
- Understanding platform differences (SQLite vs PostgreSQL, browser differences)

The codebase is now more robust, with better error handling, logging, and documentation to prevent and debug future issues.
