# 🧪 Test Suite Documentation

## Overview

Comprehensive test suite for the Lead Generation Chatbot to verify conversation flow, stage transitions, lead extraction, and qualification logic.

---

## 📁 Test Structure

```
chatbot_backend/
├── chat/
│   └── tests/
│       ├── __init__.py
│       └── test_conversation_flow.py  ← Main test file
└── run_tests.py  ← Test runner script
```

---

## 🎯 What is Being Tested

### 1. **Conversation Flow Tests** (`ConversationFlowTestCase`)

Tests the complete API endpoint flow from HTTP request to JSON response.

| Test                                                   | Description                                   | Verification                       |
| ------------------------------------------------------ | --------------------------------------------- | ---------------------------------- |
| `test_01_greeting_to_discovery_transition`             | First message moves from greeting → discovery | Stage progression, DB persistence  |
| `test_02_discovery_with_intent_extraction`             | Intent extraction during discovery            | Lead data extraction, intent_level |
| `test_03_qualification_with_email_collection`          | Email collection triggers qualification       | Lead creation, qualified flag      |
| `test_04_full_conversation_flow`                       | Complete flow: greeting → discovery → contact | End-to-end stage progression       |
| `test_05_qualification_logic_medium_intent_with_email` | Medium intent + email = qualified             | Business logic validation          |
| `test_06_qualification_logic_high_intent_no_contact`   | High intent but no contact = not qualified    | Edge case handling                 |
| `test_07_qualification_logic_low_intent_with_email`    | Low intent + email = not qualified            | Qualification rule enforcement     |
| `test_08_lead_idempotency`                             | Same email doesn't create duplicate leads     | Idempotent lead creation           |

### 2. **LangGraph Node Tests** (`LangGraphNodeTestCase`)

Tests individual node logic in isolation.

| Test                                               | Node           | Verification                              |
| -------------------------------------------------- | -------------- | ----------------------------------------- |
| `test_stage_analyzer_greeting_to_discovery`        | stage_analyzer | greeting → discovery transition           |
| `test_stage_analyzer_discovery_with_medium_intent` | stage_analyzer | discovery → qualification (medium intent) |
| `test_stage_analyzer_discovery_with_low_intent`    | stage_analyzer | discovery stays (low intent)              |
| `test_stage_updater_high_intent_with_email`        | stage_updater  | High intent + email → contact + qualified |
| `test_stage_updater_medium_intent_no_contact`      | stage_updater  | Medium intent no contact → qualification  |

### 3. **Database Persistence Tests** (`DatabasePersistenceTestCase`)

Tests database operations and data integrity.

| Test                               | Verification                            |
| ---------------------------------- | --------------------------------------- |
| `test_conversation_creation`       | Conversation created on first message   |
| `test_message_persistence`         | User and bot messages saved             |
| `test_lead_persistence_with_email` | Lead created and linked to conversation |

### 4. **Edge Case Tests** (`EdgeCaseTestCase`)

Tests error handling and boundary conditions.

| Test                               | Scenario                                 |
| ---------------------------------- | ---------------------------------------- |
| `test_missing_session_id`          | API returns 400 when session_id missing  |
| `test_missing_data`                | API returns 400 when data missing        |
| `test_empty_bot_response_fallback` | Fallback response when LLM returns empty |
| `test_invalid_json_from_llm`       | Graceful handling of malformed JSON      |

---

## 🚀 How to Run Tests

### Run All Tests

```bash
cd chatbot_backend
python run_tests.py
```

### Run with Verbose Output

```bash
python run_tests.py --verbose
```

### Run Specific Test Class

```bash
python run_tests.py ConversationFlowTestCase
```

### Run Using Django Test Command

```bash
python manage.py test chat.tests
```

### Run Single Test Method

```bash
python manage.py test chat.tests.test_conversation_flow.ConversationFlowTestCase.test_01_greeting_to_discovery_transition
```

---

## ✅ Expected Test Results

### Success Output Example

```
======================================================================
LEAD GENERATION CHATBOT - TEST SUITE
======================================================================

Running tests...
............................
----------------------------------------------------------------------
Ran 18 tests in 3.245s

OK

======================================================================
TEST SUITE COMPLETE
======================================================================
```

### What Each Test Validates

#### **Stage Progression Logic**

✅ greeting → discovery (automatic on first real message)  
✅ discovery → qualification (when intent_level = medium/high)  
✅ qualification → contact (when email or phone provided)  
✅ contact → closing (when qualified = true)

#### **Lead Extraction**

✅ LLM extracts structured data from user messages  
✅ JSON parsing handles malformed LLM output gracefully  
✅ Lead data persists to database correctly  
✅ Duplicate emails don't create new leads (idempotent)

#### **Qualification Logic**

✅ `qualified = true` when: `intent_level in ["medium", "high"] AND (email OR phone)`  
✅ `qualified = false` when: low intent OR missing contact info

#### **Database Safety**

✅ No LLM calls inside transactions  
✅ Atomic blocks protect data integrity  
✅ Message history persists correctly  
✅ Lead-conversation relationship maintained

---

## 🔍 Test Coverage

### Files Covered

- ✅ `chat/views.py` (API endpoint)
- ✅ `chat/services/conversation_graph.py` (LangGraph structure)
- ✅ `chat/services/langgraph_nodes/stage_analyzer.py`
- ✅ `chat/services/langgraph_nodes/response_generator.py`
- ✅ `chat/services/langgraph_nodes/lead_extractor.py`
- ✅ `chat/services/langgraph_nodes/stage_updater.py`
- ✅ `chat/services/lead_extraction.py`
- ✅ `chat/models.py` (Conversation, Message, Lead)

### Scenarios Covered

| Scenario                               | Covered |
| -------------------------------------- | ------- |
| First-time user                        | ✅      |
| Returning user (existing conversation) | ✅      |
| User provides email                    | ✅      |
| User provides phone                    | ✅      |
| High intent user                       | ✅      |
| Low intent user                        | ✅      |
| Invalid input                          | ✅      |
| LLM failures                           | ✅      |

---

## 🐛 Debugging Failed Tests

### If `test_01_greeting_to_discovery_transition` fails:

- Check if `stage_analyzer_node` is executing
- Verify `state.should_extract_lead` flag logic
- Check logging output for stage transitions

### If `test_03_qualification_with_email_collection` fails:

- Verify `lead_extractor_node` is extracting email correctly
- Check `stage_updater_node` logic for contact stage
- Verify qualification rule: `intent in ["medium", "high"] AND contact_info`

### If lead persistence tests fail:

- Check database migrations are applied: `python manage.py migrate`
- Verify `Lead.objects.get_or_create()` logic
- Check transaction isolation

---

## 📊 Understanding Test Output

### Verbose Output Example

```
test_01_greeting_to_discovery_transition (chat.tests.test_conversation_flow.ConversationFlowTestCase)
Test: greeting stage → discovery stage transition ...
[Stage Analyzer] Starting analysis | Current Stage: greeting
[Stage Analyzer] Transition: greeting → discovery
[Response Generator] Starting | Stage: discovery
[Lead Extractor] Starting | Should Extract: True
[Stage Updater] Complete | Final Stage: discovery | Qualified: False
ok

test_02_discovery_with_intent_extraction (chat.tests.test_conversation_flow.ConversationFlowTestCase)
Test: discovery stage with medium/high intent → qualification ...
[Stage Analyzer] Intent level medium detected → Moving to qualification
[Lead Extractor] Complete | Intent: medium | Email: False | Phone: False | Qualified: False
ok
```

---

## 🎯 Key Assertions

### Stage Transition Assertions

```python
self.assertEqual(data["data"]["stage"], "discovery")
self.assertEqual(conversation.stage, "discovery")
```

### Lead Qualification Assertions

```python
self.assertTrue(data["data"]["lead"]["qualified"])
self.assertEqual(data["data"]["lead"]["intent_level"], "high")
self.assertEqual(data["data"]["lead"]["email"], "john@example.com")
```

### Database Persistence Assertions

```python
self.assertEqual(messages.count(), 2)  # user + bot
self.assertEqual(Lead.objects.filter(email="test@example.com").count(), 1)
self.assertEqual(conversation.lead, lead)
```

---

## 🔧 Maintenance

### Adding New Tests

1. Add test method to appropriate test class
2. Follow naming convention: `test_##_descriptive_name`
3. Use `@patch` for LLM mocking
4. Clean up in `tearDown()` method

### Mocking LLM Responses

```python
@patch('chat.utils.generate_llm_response')
def test_example(self, mock_llm):
    mock_llm.return_value = {
        "summary": "Bot response",
        "duration": "1.2s"
    }
    # Test logic here
```

### Testing Lead Extraction

```python
mock_llm.return_value = {
    "summary": json.dumps({
        "intent_level": "high",
        "email": "test@example.com",
        "phone": None,
        "company": "TestCorp",
        "problem": "Need automation"
    }),
    "duration": "0.8s"
}
```

---

## 📝 Test Best Practices

1. **Isolation**: Each test is independent, no shared state
2. **Cleanup**: `tearDown()` deletes all test data
3. **Mocking**: LLM calls are mocked to avoid external dependencies
4. **Assertions**: Multiple assertions per test for comprehensive validation
5. **Naming**: Descriptive test names explain what is being tested

---

## 🎓 Understanding the Tests

### Why Mock LLM Calls?

- **Speed**: Tests run instantly without waiting for LLM
- **Reliability**: Tests don't fail due to LLM issues
- **Predictability**: Controlled responses for consistent testing
- **Cost**: No API calls to external services

### What is Actually Tested?

Even with mocked LLMs, we're testing:

- ✅ State transitions through LangGraph
- ✅ Database operations and persistence
- ✅ API endpoint request/response handling
- ✅ Business logic (qualification rules)
- ✅ Error handling and edge cases

### What is NOT Tested?

- ❌ Actual LLM response quality
- ❌ Prompt engineering effectiveness
- ❌ Real-world LLM failures (timeouts, rate limits)

For those scenarios, use **integration tests** or **manual testing** with real LLM.

---

## 🚨 Common Issues

### Issue: Tests fail with "No module named 'chat.tests'"

**Solution**: Ensure `__init__.py` exists in `chat/tests/` directory

### Issue: Database errors during tests

**Solution**: Run migrations: `python manage.py migrate`

### Issue: Import errors

**Solution**: Ensure Django environment is set up: `export DJANGO_SETTINGS_MODULE=chatbot_backend.settings`

### Issue: LLM calls not being mocked

**Solution**: Check `@patch` decorator path matches actual import path

---

## 📚 Further Reading

- [Django Testing Documentation](https://docs.djangoproject.com/en/stable/topics/testing/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [LangGraph Testing Best Practices](https://langchain-ai.github.io/langgraph/testing/)

---

**Last Updated**: January 8, 2026
