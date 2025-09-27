import pytest
from unittest.mock import MagicMock, patch
from app import app, handle_schedule_meeting, execute_function_call, handle_gemini_response
import datetime

# --- Fixtures ---

@pytest.fixture
def client():
    """Create a Flask test client."""
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def mock_gemini_response_function_call():
    """Fixture for a mock Gemini response with a function call."""
    response = MagicMock()
    function_call = MagicMock()
    function_call.name = 'schedule_meeting'
    function_call.args = {
        'topic': 'Test Meeting',
        'date': '2025-12-25',
        'time': '14:00'
    }
    response.candidates = [MagicMock()]
    response.candidates[0].content.parts = [MagicMock()]
    response.candidates[0].content.parts[0].function_call = function_call
    return response

@pytest.fixture
def mock_gemini_response_text():
    """Fixture for a mock Gemini response with only text."""
    response = MagicMock()
    response.candidates = [MagicMock()]
    response.candidates[0].content.parts = [MagicMock()]
    response.candidates[0].content.parts[0].function_call = None
    response.text = "This is a text response."
    return response

# --- Unit Tests ---

def test_handle_schedule_meeting_success(mocker):
    """Test successful event creation."""
    mocker.patch('app.get_credentials', return_value='dummy_creds')
    mock_create_event = mocker.patch('app.create_event', return_value={'id': '123', 'summary': 'Test Meeting'})
    
    args = {
        'topic': 'Test Meeting',
        'date': '2025-12-25',
        'time': '14:00'
    }
    
    with app.app_context():
        response, status_code = handle_schedule_meeting(args)

    assert status_code == 200
    json_data = response.get_json()
    assert json_data['response'] == "I've scheduled a meeting about 'Test Meeting'. Quack."
    assert json_data['event']['id'] == '123'
    
    start_time = datetime.datetime(2025, 12, 25, 14, 0)
    end_time = start_time + datetime.timedelta(hours=1)
    mock_create_event.assert_called_once_with('dummy_creds', 'Test Meeting', start_time, end_time)

def test_handle_schedule_meeting_no_creds(mocker):
    """Test the case where Google Calendar credentials are not available."""
    mocker.patch('app.get_credentials', return_value=None)
    mocker.patch('app.authorize_flow', return_value='http://auth.url')

    with app.app_context():
        response, status_code = handle_schedule_meeting({})

    assert status_code == 200
    json_data = response.get_json()
    assert json_data['response'] == "I need to authorize with your Google Calendar first."
    assert json_data['authorization_url'] == 'http://auth.url'

def test_execute_function_call(mocker):
    """Test the function call router."""
    mock_handler = mocker.patch('app.handle_schedule_meeting', return_value='OK')
    
    function_call = MagicMock()
    function_call.name = 'schedule_meeting'
    function_call.args = {'key': 'value'}
    
    result = execute_function_call(function_call)
    
    mock_handler.assert_called_once_with({'key': 'value'})
    assert result == 'OK'

def test_handle_gemini_response_with_function_call(mocker, mock_gemini_response_function_call):
    """Test handling a Gemini response that contains a function call."""
    mock_executor = mocker.patch('app.execute_function_call', return_value='Executed')
    
    result = handle_gemini_response(mock_gemini_response_function_call)
    
    mock_executor.assert_called_once()
    assert result == 'Executed'

def test_handle_gemini_response_with_text(mocker, mock_gemini_response_text):
    """Test handling a Gemini response that is only text."""
    with app.app_context():
        response, status_code = handle_gemini_response(mock_gemini_response_text)
    
    assert status_code == 200
    assert response.get_json()['response'] == "This is a text response. Quack."

# --- Integration Tests ---

@patch('app.auth.verify_id_token')
@patch('app.client.models.generate_content')
def test_toolcall_endpoint_success(mock_generate_content, mock_verify_token, client, mock_gemini_response_function_call):
    """Test the /api/toolcall endpoint from end-to-end with a function call."""
    mock_verify_token.return_value = {'uid': 'test_user'}
    mock_generate_content.return_value = mock_gemini_response_function_call
    
    # We also need to mock the calendar functions for the integration test
    with patch('app.get_credentials', return_value='dummy_creds'), \
         patch('app.create_event', return_value={'id': '123'}):
        
        response = client.post('/api/toolcall', 
                               json={'prompt': 'schedule a meeting'},
                               headers={'Authorization': 'Bearer test_token'})

    assert response.status_code == 200
    json_data = response.get_json()
    assert "I've scheduled a meeting" in json_data['response']
    assert json_data['event']['id'] == '123'

def test_toolcall_endpoint_unauthorized(client):
    """Test that the endpoint returns 401 if no token is provided."""
    response = client.post('/api/toolcall', json={'prompt': 'test'})
    assert response.status_code == 401
    assert response.get_json()['error'] == 'Unauthorized'
