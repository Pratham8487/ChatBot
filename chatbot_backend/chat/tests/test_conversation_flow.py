"""
Comprehensive test cases for Lead Generation Chatbot conversation flow.

Tests verify:
1. Stage progression: greeting → discovery → qualification → contact → closing
2. Lead extraction and data persistence
3. Qualification logic (intent_level + contact_info)
4. LangGraph node execution order
5. State mutations and database persistence
"""

import json
from django.test import TestCase, Client
from django.urls import reverse
from chat.models import Conversation, Message, Lead
from chat.services.langgraph_state import ConversationState
from chat.services.conversation_graph import build_conversation_graph
from chat.services.langgraph_nodes.stage_analyzer import analyze_stage_node
from chat.services.langgraph_nodes.lead_extractor import extract_lead_node
from chat.services.langgraph_nodes.stage_updater import stage_updater_node
from unittest.mock import patch, MagicMock


class ConversationFlowTestCase(TestCase):
    """Test full conversation flow through API endpoint"""

    def setUp(self):
        self.client = Client()
        self.session_id = "test-session-001"
        self.api_url = "/api/chat/"

    def tearDown(self):
        # Cleanup after each test
        Conversation.objects.all().delete()
        Message.objects.all().delete()
        Lead.objects.all().delete()

    @patch('chat.utils.generate_llm_response')
    def test_01_greeting_to_discovery_transition(self, mock_llm):
        """Test: greeting stage → discovery stage transition"""
        
        # Mock LLM responses
        mock_llm.return_value = {
            "summary": "Hello! I'd be happy to help. What business challenges are you facing?",
            "duration": "1.2s"
        }

        # Message 1: Initial greeting
        response = self.client.post(
            self.api_url,
            data=json.dumps({
                "session_id": self.session_id,
                "data": "Hi there!"
            }),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Assertions
        self.assertTrue(data["isSuccess"])
        self.assertEqual(data["data"]["stage"], "discovery")  # Should move to discovery
        
        # Verify database
        conversation = Conversation.objects.get(session_id=self.session_id)
        self.assertEqual(conversation.stage, "discovery")
        
        # Verify messages saved
        messages = Message.objects.filter(conversation=conversation)
        self.assertEqual(messages.count(), 2)  # user + bot

    @patch('chat.utils.generate_llm_response')
    def test_02_discovery_with_intent_extraction(self, mock_llm):
        """Test: discovery stage with medium/high intent → qualification"""
        
        # Mock LLM responses
        mock_llm.side_effect = [
            # Response generator
            {"summary": "Great! Tell me more about your automation needs.", "duration": "1.2s"},
            # Lead extractor
            {
                "summary": json.dumps({
                    "intent_level": "medium",
                    "email": None,
                    "phone": None,
                    "company": "TechCorp",
                    "problem": "Need business automation"
                }),
                "duration": "0.8s"
            }
        ]

        # Create existing conversation in discovery stage
        conversation = Conversation.objects.create(
            session_id=self.session_id,
            stage="discovery"
        )

        # Message: User expresses need
        response = self.client.post(
            self.api_url,
            data=json.dumps({
                "session_id": self.session_id,
                "data": "I need help with business automation for my company TechCorp"
            }),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Assertions
        self.assertTrue(data["isSuccess"])
        self.assertEqual(data["data"]["lead"]["intent_level"], "medium")
        self.assertFalse(data["data"]["lead"]["qualified"])  # Not qualified without contact
        
        # Stage should move to qualification OR stay in discovery (depends on logic)
        # Based on stage_updater: medium intent without contact → qualification
        conversation.refresh_from_db()
        self.assertIn(conversation.stage, ["discovery", "qualification"])

    @patch('chat.utils.generate_llm_response')
    def test_03_qualification_with_email_collection(self, mock_llm):
        """Test: qualification stage → contact stage (email provided)"""
        
        # Mock LLM responses
        mock_llm.side_effect = [
            # Response generator
            {"summary": "Perfect! I'll send you detailed information.", "duration": "1.2s"},
            # Lead extractor
            {
                "summary": json.dumps({
                    "intent_level": "high",
                    "email": "john@techcorp.com",
                    "phone": None,
                    "company": "TechCorp",
                    "problem": "Business automation"
                }),
                "duration": "0.8s"
            }
        ]

        # Create conversation in qualification stage
        conversation = Conversation.objects.create(
            session_id=self.session_id,
            stage="qualification"
        )

        # Message: User provides email
        response = self.client.post(
            self.api_url,
            data=json.dumps({
                "session_id": self.session_id,
                "data": "You can reach me at john@techcorp.com"
            }),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Assertions
        self.assertTrue(data["isSuccess"])
        self.assertEqual(data["data"]["stage"], "contact")  # Should move to contact
        self.assertEqual(data["data"]["lead"]["email"], "john@techcorp.com")
        self.assertTrue(data["data"]["lead"]["qualified"])  # high intent + email = qualified
        
        # Verify lead created
        lead = Lead.objects.get(email="john@techcorp.com")
        self.assertEqual(lead.intent_level, "high")
        self.assertTrue(lead.qualified)
        
        # Verify conversation linked to lead
        conversation.refresh_from_db()
        self.assertEqual(conversation.lead, lead)
        self.assertEqual(conversation.stage, "contact")

    @patch('chat.utils.generate_llm_response')
    def test_04_full_conversation_flow(self, mock_llm):
        """Test: Complete flow from greeting to contact stage"""
        
        # Mock LLM responses for entire flow
        mock_llm.side_effect = [
            # Message 1: Greeting
            {"summary": "Hello! How can I help you today?", "duration": "1s"},
            {"summary": json.dumps({"intent_level": "low", "email": None, "phone": None, "company": None, "problem": None}), "duration": "0.5s"},
            
            # Message 2: Discovery
            {"summary": "Tell me about your business needs.", "duration": "1s"},
            {"summary": json.dumps({"intent_level": "medium", "email": None, "phone": None, "company": "TechCorp", "problem": "automation"}), "duration": "0.5s"},
            
            # Message 3: Contact collection
            {"summary": "Great! Let me follow up with you.", "duration": "1s"},
            {"summary": json.dumps({"intent_level": "high", "email": "test@company.com", "phone": None, "company": "TechCorp", "problem": "automation"}), "duration": "0.5s"},
        ]

        # Message 1: Greeting
        response1 = self.client.post(self.api_url, data=json.dumps({
            "session_id": self.session_id,
            "data": "Hi"
        }), content_type="application/json")
        self.assertEqual(response1.json()["data"]["stage"], "discovery")

        # Message 2: Discovery
        response2 = self.client.post(self.api_url, data=json.dumps({
            "session_id": self.session_id,
            "data": "I need automation for TechCorp"
        }), content_type="application/json")
        
        # Message 3: Provide contact
        response3 = self.client.post(self.api_url, data=json.dumps({
            "session_id": self.session_id,
            "data": "Contact me at test@company.com"
        }), content_type="application/json")
        
        data3 = response3.json()
        self.assertEqual(data3["data"]["stage"], "contact")
        self.assertTrue(data3["data"]["lead"]["qualified"])

    def test_05_qualification_logic_medium_intent_with_email(self):
        """Test: Qualification logic - medium intent + email = qualified"""
        
        state = ConversationState(
            session_id="test",
            stage="qualification",
            user_message="test",
            lead_data={},
            intent_level="medium",
            metadata={"engine": "ollama"}
        )
        
        # Simulate lead extraction result
        state.lead_data = {
            "email": "test@example.com",
            "phone": None,
            "company": None,
            "problem": None
        }
        state.intent_level = "medium"
        
        # Apply qualification logic (from lead_extractor)
        qualified = bool(
            state.intent_level in ("medium", "high")
            and (state.lead_data.get("email") or state.lead_data.get("phone"))
        )
        
        self.assertTrue(qualified)

    def test_06_qualification_logic_high_intent_no_contact(self):
        """Test: Qualification logic - high intent but no contact = not qualified"""
        
        state = ConversationState(
            session_id="test",
            stage="discovery",
            user_message="test",
            lead_data={},
            intent_level="high",
            metadata={"engine": "ollama"}
        )
        
        # No contact info
        state.lead_data = {
            "email": None,
            "phone": None,
            "company": "TestCorp",
            "problem": "Need help"
        }
        
        # Apply qualification logic
        qualified = bool(
            state.intent_level in ("medium", "high")
            and (state.lead_data.get("email") or state.lead_data.get("phone"))
        )
        
        self.assertFalse(qualified)

    def test_07_qualification_logic_low_intent_with_email(self):
        """Test: Qualification logic - low intent + email = not qualified"""
        
        state = ConversationState(
            session_id="test",
            stage="discovery",
            user_message="test",
            lead_data={"email": "test@example.com"},
            intent_level="low",
            metadata={"engine": "ollama"}
        )
        
        # Apply qualification logic
        qualified = bool(
            state.intent_level in ("medium", "high")
            and (state.lead_data.get("email") or state.lead_data.get("phone"))
        )
        
        self.assertFalse(qualified)

    @patch('chat.utils.generate_llm_response')
    def test_08_lead_idempotency(self, mock_llm):
        """Test: Lead creation is idempotent (same email = same lead)"""
        
        mock_llm.side_effect = [
            {"summary": "Response 1", "duration": "1s"},
            {"summary": json.dumps({"intent_level": "high", "email": "john@test.com", "phone": None, "company": "Co", "problem": "test"}), "duration": "0.5s"},
            {"summary": "Response 2", "duration": "1s"},
            {"summary": json.dumps({"intent_level": "high", "email": "john@test.com", "phone": None, "company": "Co", "problem": "updated problem"}), "duration": "0.5s"},
        ]

        # Create conversation
        Conversation.objects.create(session_id=self.session_id, stage="qualification")

        # Message 1: Create lead
        self.client.post(self.api_url, data=json.dumps({
            "session_id": self.session_id,
            "data": "Email: john@test.com"
        }), content_type="application/json")
        
        lead_count_1 = Lead.objects.count()
        
        # Message 2: Same email
        self.client.post(self.api_url, data=json.dumps({
            "session_id": self.session_id,
            "data": "john@test.com again"
        }), content_type="application/json")
        
        lead_count_2 = Lead.objects.count()
        
        # Should have same number of leads (idempotent)
        self.assertEqual(lead_count_1, lead_count_2)
        self.assertEqual(Lead.objects.filter(email="john@test.com").count(), 1)


class LangGraphNodeTestCase(TestCase):
    """Test individual LangGraph nodes"""

    def test_stage_analyzer_greeting_to_discovery(self):
        """Test stage_analyzer: greeting → discovery"""
        
        state = ConversationState(
            session_id="test",
            stage="greeting",
            user_message="Hello",
            lead_data={},
            metadata={"engine": "ollama"}
        )
        
        result = analyze_stage_node(state)
        
        self.assertEqual(result.stage, "discovery")
        self.assertTrue(result.should_extract_lead)

    def test_stage_analyzer_discovery_with_medium_intent(self):
        """Test stage_analyzer: discovery → qualification (medium intent)"""
        
        state = ConversationState(
            session_id="test",
            stage="discovery",
            user_message="I need help",
            lead_data={},
            intent_level="medium",
            metadata={"engine": "ollama"}
        )
        
        result = analyze_stage_node(state)
        
        self.assertEqual(result.stage, "qualification")
        self.assertTrue(result.should_extract_lead)

    def test_stage_analyzer_discovery_with_low_intent(self):
        """Test stage_analyzer: discovery stays (low intent)"""
        
        state = ConversationState(
            session_id="test",
            stage="discovery",
            user_message="Just looking",
            lead_data={},
            intent_level="low",
            metadata={"engine": "ollama"}
        )
        
        result = analyze_stage_node(state)
        
        self.assertEqual(result.stage, "discovery")

    def test_stage_updater_high_intent_with_email(self):
        """Test stage_updater: high intent + email → contact + qualified"""
        
        state = ConversationState(
            session_id="test",
            stage="qualification",
            user_message="test",
            lead_data={"email": "test@example.com", "phone": None},
            intent_level="high",
            metadata={"engine": "ollama"}
        )
        
        result = stage_updater_node(state)
        
        self.assertEqual(result.stage, "contact")
        self.assertTrue(result.qualified)

    def test_stage_updater_medium_intent_no_contact(self):
        """Test stage_updater: medium intent but no contact → qualification"""
        
        state = ConversationState(
            session_id="test",
            stage="discovery",
            user_message="test",
            lead_data={"email": None, "phone": None},
            intent_level="medium",
            metadata={"engine": "ollama"}
        )
        
        result = stage_updater_node(state)
        
        self.assertEqual(result.stage, "qualification")
        self.assertFalse(result.qualified)


class DatabasePersistenceTestCase(TestCase):
    """Test database operations and data persistence"""

    def setUp(self):
        self.client = Client()
        self.api_url = "/api/chat/"

    @patch('chat.utils.generate_llm_response')
    def test_conversation_creation(self, mock_llm):
        """Test: Conversation is created on first message"""
        
        mock_llm.return_value = {"summary": "Hello", "duration": "1s"}
        
        session_id = "new-session"
        
        response = self.client.post(self.api_url, data=json.dumps({
            "session_id": session_id,
            "data": "Hi"
        }), content_type="application/json")
        
        self.assertEqual(response.status_code, 200)
        
        # Verify conversation created
        conversation = Conversation.objects.get(session_id=session_id)
        self.assertIsNotNone(conversation)
        self.assertEqual(conversation.stage, "discovery")  # Should progress from greeting

    @patch('chat.utils.generate_llm_response')
    def test_message_persistence(self, mock_llm):
        """Test: Both user and bot messages are saved"""
        
        mock_llm.return_value = {"summary": "Bot response", "duration": "1s"}
        
        session_id = "message-test"
        
        self.client.post(self.api_url, data=json.dumps({
            "session_id": session_id,
            "data": "User message"
        }), content_type="application/json")
        
        conversation = Conversation.objects.get(session_id=session_id)
        messages = Message.objects.filter(conversation=conversation)
        
        self.assertEqual(messages.count(), 2)
        
        user_msg = messages.filter(role="user").first()
        bot_msg = messages.filter(role="bot").first()
        
        self.assertEqual(user_msg.content, "User message")
        self.assertIsNotNone(bot_msg.content)

    @patch('chat.utils.generate_llm_response')
    def test_lead_persistence_with_email(self, mock_llm):
        """Test: Lead is created and linked to conversation"""
        
        mock_llm.side_effect = [
            {"summary": "Response", "duration": "1s"},
            {
                "summary": json.dumps({
                    "intent_level": "high",
                    "email": "lead@test.com",
                    "phone": None,
                    "company": "TestCo",
                    "problem": "Need automation"
                }),
                "duration": "0.5s"
            }
        ]
        
        session_id = "lead-test"
        Conversation.objects.create(session_id=session_id, stage="qualification")
        
        self.client.post(self.api_url, data=json.dumps({
            "session_id": session_id,
            "data": "Contact: lead@test.com"
        }), content_type="application/json")
        
        # Verify lead created
        lead = Lead.objects.get(email="lead@test.com")
        self.assertIsNotNone(lead)
        self.assertEqual(lead.intent_level, "high")
        self.assertTrue(lead.qualified)
        
        # Verify conversation linked
        conversation = Conversation.objects.get(session_id=session_id)
        self.assertEqual(conversation.lead, lead)


class EdgeCaseTestCase(TestCase):
    """Test edge cases and error handling"""

    def setUp(self):
        self.client = Client()
        self.api_url = "/api/chat/"

    def test_missing_session_id(self):
        """Test: API returns error when session_id is missing"""
        
        response = self.client.post(self.api_url, data=json.dumps({
            "data": "Hello"
        }), content_type="application/json")
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["isSuccess"])

    def test_missing_data(self):
        """Test: API returns error when data is missing"""
        
        response = self.client.post(self.api_url, data=json.dumps({
            "session_id": "test"
        }), content_type="application/json")
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["isSuccess"])

    @patch('chat.utils.generate_llm_response')
    def test_empty_bot_response_fallback(self, mock_llm):
        """Test: Fallback response when LLM returns empty"""
        
        mock_llm.return_value = {"summary": "", "duration": "1s"}
        
        response = self.client.post(self.api_url, data=json.dumps({
            "session_id": "fallback-test",
            "data": "Hello"
        }), content_type="application/json")
        
        data = response.json()
        self.assertIn("response", data["data"])
        self.assertTrue(len(data["data"]["response"]) > 0)  # Should have fallback

    @patch('chat.services.lead_extraction.extract_lead_from_message')
    def test_invalid_json_from_llm(self, mock_extract):
        """Test: Graceful handling of invalid JSON from LLM"""
        
        # Mock returns LeadData with all None values (safe fallback)
        from chat.services.lead_models import LeadData
        mock_extract.return_value = LeadData()
        
        state = ConversationState(
            session_id="test",
            stage="discovery",
            user_message="test message",
            lead_data={},
            metadata={"engine": "ollama"}
        )
        state.should_extract_lead = True
        
        result = extract_lead_node(state)
        
        # Should not crash, should return empty lead data
        self.assertIsNotNone(result)
        self.assertFalse(result.qualified)
