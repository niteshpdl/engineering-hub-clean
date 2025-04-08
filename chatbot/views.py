import json
import os
import uuid
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import google.generativeai as genai
from dotenv import load_dotenv
import PyPDF2
import io
import tempfile
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from django.shortcuts import render
import traceback
from django.db.models import Q
from django.conf import settings

from chatbot.models import ChatMessage, ChatSession
# Import models from notes app
from notes.models import Resource, Department, Semester, Project


load_dotenv()
# Load environment variables if not already loaded
load_dotenv()

# Set Gemini API key from environment
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Initialize the Gemini model
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"Error initializing Gemini model: {str(e)}")
    model = None


# In-memory session storage (replace with database in production)
SESSIONS = {}

def list_available_models():
    """List all available Gemini models"""
    try:
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            print("API key not found")
            return []
        
        genai.configure(api_key=api_key)
        models = genai.list_models()
        
        available_models = []
        for model in models:
            available_models.append(model.name)
            print(f"Available model: {model.name}")
        
        return available_models
    except Exception as e:
        print(f"Error listing models: {str(e)}")
        return []

# Call this function during startup
list_available_models()



def get_response(message, session=None):
    """Get response from Gemini with conversation history"""
    try:
        # Load environment variables directly
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            return "I'm sorry, the AI service is currently unavailable. Please check your API key configuration."
        
        # If session is provided, get conversation history
        conversation_history = []
        if session:
            # Get the last 10 messages from this session
            previous_messages = ChatMessage.objects.filter(session=session).order_by('created_at')[:10]
            
            for msg in previous_messages:
                if msg.is_bot:
                    conversation_history.append({"role": "model", "parts": [msg.content]})
                else:
                    conversation_history.append({"role": "user", "parts": [msg.content]})
        
        # Initialize Gemini with the API key from environment
        genai.configure(api_key=api_key)
        
        # Use the correct model name from our list
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Add formatting instructions to the message
        formatting_instructions = """
        Please format your response in a clean, readable way:
        - Use paragraphs for better readability
        - Avoid using markdown-style formatting like **bold** or *italics*
        - Use HTML tags like <strong> for emphasis instead
        - For lists, use proper HTML formatting with <ul> and <li> tags
        - Keep your response concise and well-structured
        """
        
        enhanced_message = f"{message}\n\n{formatting_instructions}"
        
        # Start a chat session with history if available
        if conversation_history:
            chat = model.start_chat(history=conversation_history)
            response = chat.send_message(message)  # Use original message for chat
        else:
            # No history, just send the enhanced message
            response = model.generate_content(enhanced_message)
        
        return response.text
    except Exception as e:
        print(f"Error getting response from Gemini: {str(e)}")
        traceback.print_exc()
        
        # Error handling...
        return f"I'm sorry, I encountered an error: {str(e)}"


def get_session_data(session_id):
    """Get session data from storage"""
    return SESSIONS.get(session_id)


def save_session_data(session_id, data):
    """Save session data to storage"""
    SESSIONS[session_id] = data


def gemini_chat(messages):
    """Process chat with Gemini model"""
    try:
        if not model:
            return "Sorry, the AI model is not properly configured. Please check the server logs."
            
        # Convert messages to Gemini format
        gemini_messages = []
        for msg in messages:
            role = "user" if msg['role'] == 'user' else "model"
            gemini_messages.append({"role": role, "parts": [msg['content']]})
        
        # Generate response
        response = model.generate_content(gemini_messages)
        return response.text
    except Exception as e:
        print(f"Error in Gemini chat: {str(e)}")
        return "I'm sorry, I encountered an error processing your request."


def extract_text_from_pdf(pdf_file):
    """Extract text from a PDF file"""
    try:
        # Create a temporary file to handle the uploaded file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in pdf_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        # Open the PDF file
        text = ""
        with open(temp_file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            # Extract text from each page
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n\n"
        
        # Delete the temporary file
        os.unlink(temp_file_path)
        
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        return "Error extracting text from PDF."


def search_resources(query):
    """
    Search for resources in the database based on a text query
    Returns a dict with search results
    """
    try:
        print(f"Searching resources for query: '{query}'")
        
        # Original query for logging
        original_query = query
        query_lower = query.lower()
        
        # Look for resource types in the query
        resource_types = {
            'notes': ['note', 'notes', 'lecture'],
            'handwritten': ['handwritten', 'written', 'handwriting', 'Handwritten Notes', 'Handwritten'],
            'insight': ['insight', 'insights', 'summary'],
            'syllabus': ['syllabus', 'curriculum', 'course outline', 'course content', 'outline']
        }
        
        # Determine which resource type was requested
        requested_type = None
        for resource_type, keywords in resource_types.items():
            if any(keyword in query_lower for keyword in keywords):
                requested_type = resource_type
                print(f"Detected resource type: {resource_type}")
                break
        
        # Create base query
        resources_query = Resource.objects.all()
        
        # Apply resource_type filter if applicable
        if requested_type:
            print(f"Filtering by resource type: {requested_type}")
            resources_query = resources_query.filter(resource_type=requested_type)
        
        # Check for specific resources that might be problematic
        print("Checking for specific resources...")
        specific_checks = ["antenna and propagation", "antenna & propagation"]
        for check in specific_checks:
            if check in query_lower:
                print(f"Detected specific search for: '{check}'")
                specific_check = resources_query.filter(title__icontains=check)
                if specific_check.exists():
                    print(f"Found {specific_check.count()} resources with '{check}' in title")
                    for res in specific_check:
                        print(f"  - {res.id}: {res.title} ({res.resource_type})")
        
        # Extract subject from query - this is critical for finding the right resources
        # Create a copy of the query for subject extraction
        subject_query = query_lower
        
        # Remove common words to isolate the subject, but be careful not to remove important terms
        common_words = ['give', 'me', 'show', 'find', 'get', 'the', 'a', 'an', 'for', 'of', 'about', 'on']
        # Don't remove resource type words from the subject query
        for word in common_words:
            subject_query = subject_query.replace(f" {word} ", " ")
        
        subject_query = subject_query.strip()
        print(f"Extracted subject query: '{subject_query}'")
        
        # SEARCH STRATEGY 1: EXACT TITLE MATCH
        # Try to find exact matches first (case insensitive)
        exact_matches = resources_query.filter(title__iexact=subject_query)
        if exact_matches.exists():
            print(f"Found exact title matches: {exact_matches.count()}")
            results = exact_matches.order_by('-upvotes', '-uploaded_at')[:5]
            return format_results(results, requested_type)
        
        # SEARCH STRATEGY 2: CONTAINS IN TITLE
        # Try to find resources where title contains the subject query
        contains_matches = resources_query.filter(title__icontains=subject_query)
        if contains_matches.exists():
            print(f"Found title contains matches: {contains_matches.count()}")
            results = contains_matches.order_by('-upvotes', '-uploaded_at')[:5]
            return format_results(results, requested_type)
        
        # SEARCH STRATEGY 3: ORIGINAL QUERY WITHOUT PREPROCESSING
        # If subject query processing removed too much, try with original query
        if subject_query != query_lower and len(subject_query) < len(query_lower) - 10:
            print(f"Trying with original query: '{query_lower}'")
            original_matches = resources_query.filter(
                Q(title__icontains=query_lower) | 
                Q(description__icontains=query_lower)
            )
            if original_matches.exists():
                print(f"Found matches with original query: {original_matches.count()}")
                results = original_matches.order_by('-upvotes', '-uploaded_at')[:5]
                return format_results(results, requested_type)
        
        # SEARCH STRATEGY 4: WORD BY WORD SEARCH - THIS IS THE KEY FIX
        # If no direct matches, try word-by-word search
        print("No direct matches, trying word-by-word search")
        words = subject_query.split()
        
        # Include words of length 2 or more, and important abbreviations
        important_abbr = ['ai', 'ml', 'os', 'db', 'ui', 'ux', 'io', 'ip']
        significant_words = [word for word in words if len(word) > 2 or word in important_abbr]
        
        if significant_words:
            print(f"Significant words for search: {significant_words}")
            
            # Build a complex query for title and description
            title_filter = None
            desc_filter = None
            
            # Define technical terms
            technical_terms = ['antenna', 'propagation', 'digital', 'analog', 'system', 'embedded', 
                             'communication', 'circuit', 'processor', 'signal', 'microcontroller', 
                             'electromagnetic', 'control', 'power', 'software', 'hardware']
            
            for word in significant_words:
                print(f"Searching for word: '{word}'")
                
                # Skip common words but NOT technical terms
                if word.lower() in common_words and word.lower() not in technical_terms:
                    continue
                
                # For the first significant word, initialize the filter
                if title_filter is None:
                    title_filter = Q(title__icontains=word)
                    desc_filter = Q(description__icontains=word)
                else:
                    # Use OR logic for title search to find partial matches
                    title_filter |= Q(title__icontains=word)
                    desc_filter |= Q(description__icontains=word)
            
            # Only proceed if we created valid filters
            if title_filter is not None and desc_filter is not None:
                combined_filter = title_filter | desc_filter
                word_matches = resources_query.filter(combined_filter)
                
                if word_matches.exists():
                    print(f"Found word-by-word matches: {word_matches.count()}")
                    results = word_matches.order_by('-upvotes', '-uploaded_at')[:5]
                    return format_results(results, requested_type)
        
        # SEARCH STRATEGY 5: FUZZY MATCHING
        # If still no results, try fuzzy matching
        print("Trying fuzzy matching...")
        
        # Get all resources (limited to a reasonable number)
        all_resources = resources_query.order_by('-upvotes')[:100]
        
        # Check each resource for partial matches
        matched_resources = []
        query_words = set(subject_query.split())
        
        # Skip fuzzy matching for very short queries or common words only
        if len(query_words) == 0 or (len(query_words) == 1 and list(query_words)[0] in 
            ['notes', 'syllabus', 'handwritten', 'insight', 'resources']):
            print("Query too generic for fuzzy matching")
            # No results found with any strategy
            print("No results found in database after all search strategies")
            return {
                'found': False,
                'resource_type': requested_type,
                'query': original_query
            }
        
        for resource in all_resources:
            # Check if resource title contains any of the query words
            title_lower = resource.title.lower()
            title_words = set(title_lower.split())
            
            # Calculate word overlap
            common_words = title_words.intersection(query_words)
            
            # Only require one significant match for technical terms
            technical_match = any(term in title_lower for term in technical_terms)
            if technical_match and len(common_words) >= 1:
                matched_resources.append(resource)
            # Otherwise require more matches for non-technical terms
            elif len(common_words) >= max(1, len(query_words) * 0.3):
                matched_resources.append(resource)
        
        if matched_resources:
            print(f"Found {len(matched_resources)} resources through fuzzy matching")
            results = resources_query.filter(id__in=[r.id for r in matched_resources])[:5]
            return format_results(results, requested_type)
        
        # No results found with any strategy
        print("No results found in database after all search strategies")
        return {
            'found': False,
            'resource_type': requested_type,
            'query': original_query
        }
    
    except Exception as e:
        print(f"Error searching resources: {str(e)}")
        traceback.print_exc()
        return {'error': str(e)}

def format_results(results, requested_type):
    """Helper function to format results consistently"""
    results_list = []
    for res in results:
        department = res.department.name if res.department else "Unknown Department"
        semester = f"Semester {res.semester.number}" if res.semester else ""
        resource_url = f"/resource/{res.id}/"
        
        results_list.append({
            'id': res.id,
            'title': res.title,
            'type': res.get_resource_type_display(),
            'department': department,
            'semester': semester,
            'url': resource_url,
            'description': res.description[:100] + '...' if res.description and len(res.description) > 100 else res.description or ""
        })
    
    return {
        'found': True,
        'count': len(results_list),
        'results': results_list,
        'resource_type': requested_type
    }


def format_resource_results(search_results, query):
    """Format search results into a readable HTML response"""
    if 'error' in search_results:
        return f"<div class='error-message'>I encountered an error while searching: {search_results['error']}</div>"
       
    if search_results.get('found', False):
        results = search_results['results']
        count = search_results['count']
        resource_type = search_results.get('resource_type') or "resource"
       
        response = f"<div class='search-results'>"
        response += f"<h3>I found {count} {resource_type} resources in our database:</h3>"
        response += "<ul class='resource-list'>"
       
        for result in results:
            response += "<li class='resource-item'>"
            response += f"<h4>{result['title']}</h4>"
            response += f"<span class='resource-type'>{result['type']}</span>"
            
            response += "<div class='resource-details'>"
            if 'department' in result and result['department']:
                response += f"<span class='department'>{result['department']}</span>"
                
            if 'semester' in result and result['semester']:
                response += f"<span class='semester'>{result['semester']}</span>"
            response += "</div>"
            
            if 'description' in result and result['description']:
                response += f"<p class='description'>{result['description']}</p>"
                
            response += f"<a href='/resource/{result['id']}/' class='resource-link' target='_blank'>View Resource</a>"
            response += "</li>"
           
        response += "</ul></div>"
        return response
    else:
        resource_type = search_results.get('resource_type') or "educational"
        return f"<div class='no-results'>I couldn't find any {resource_type} resources matching your query. Would you like to browse our available departments instead? You can also try searching with different keywords.</div>"


def test_handwritten_image(image_file):
    """Process a handwritten image file using OCR"""
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            for chunk in image_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
            
        # Process the image with Tesseract OCR
        img = Image.open(temp_file_path)
        text = pytesseract.image_to_string(img)
        
        # Delete temporary file
        os.unlink(temp_file_path)
        
        return text
    except Exception as e:
        print(f"Error processing handwritten image: {str(e)}")
        return f"Error processing image: {str(e)}"


@csrf_exempt
def process_message(request):
    """Process incoming chatbot messages"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '')
            session_id = data.get('session_id', '')
           
            # Debug logging
            print(f"Received message: '{message}' for session: {session_id}")
           
            # Validate session
            try:
                session = ChatSession.objects.get(id=session_id)
            except ChatSession.DoesNotExist:
                return JsonResponse({'error': 'Invalid session'}, status=400)
           
            # Store user message
            ChatMessage.objects.create(
                session=session,
                is_bot=False,
                content=message
            )
           
            # SIMPLIFIED APPROACH:
            # 1. Always search the database first
            search_results = search_resources(message)
            print(f"Search results: {search_results}")
            
            if search_results.get('found', False):
                # We found matching resources in the database
                print(f"Found {search_results['count']} resources in database")
                response = format_resource_results(search_results, message)
            else:
                # No resources found, use Gemini for any query
                print("No resources found, using Gemini")
                response = get_response(message, session)
           
            # Store bot response
            ChatMessage.objects.create(
                session=session,
                is_bot=True,
                content=response
            )
           
            return JsonResponse({'response': response})
           
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)
   
    return JsonResponse({'error': 'Invalid request'}, status=400)


def generate_response(message, session):
    """
    Generate a response to the user message.
    This function handles both AI responses and database searches.
    """
    try:
        # Check if this is a resource-related query
        educational_keywords = [
            'notes', 'syllabus', 'material', 'insight', 'handwritten', 
            'lecture', 'document', 'course', 'subject', 'department',
            'semester', 'engineering', 'study'
        ]
        
        is_resource_query = any(keyword in message.lower() for keyword in educational_keywords)
        
        # If it looks like a resource query, try to search the database
        if is_resource_query:
            search_results = search_resources(message)
            if search_results['found']:
                # Format the results into a nice response
                return format_resource_results(search_results, message)
        
        # If not a resource query or no results found, use Gemini
        context = "You are a helpful assistant for Engineering Hub, an educational resource website for engineering students. "
        context += "Keep your responses focused on educational topics and engineering subjects."
        
        full_prompt = f"{context}\n\nUser query: {message}"
        return get_response(full_prompt)
        
    except Exception as e:
        print(f"Error in generate_response: {str(e)}")
        traceback.print_exc()
        return f"I'm sorry, I encountered an error: {str(e)}"


# Fix the create_session function (around line 427)

@csrf_exempt
def create_session(request):
    """Create a new chat session"""
    try:
        # Create a new session
        session = ChatSession.objects.create(
            title="New Chat"
        )
       
        # Get the session ID from the model's id field
        session_id = str(session.id)
       
        # Set Engineering Hub welcome message
        welcome_message = "Hello! I'm your Engineering Hub assistant. How can I help you today?"
       
        # Store welcome message with is_bot=True
        ChatMessage.objects.create(
            session=session,
            is_bot=True,
            content=welcome_message
        )
       
        # Return both session_id and response for frontend compatibility
        return JsonResponse({
            'session_id': session_id,
            'response': welcome_message,
            'message': welcome_message
        })   
    except Exception as e:
        print(f"Error creating session: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def upload_pdf(request):
    """Upload and process a PDF file"""
    if request.method == 'POST':
        try:
            print("PDF upload request received")
            session_id = request.POST.get('session_id')
            message = request.POST.get('message', '')
            pdf_file = request.FILES.get('pdf_file')
            
            print(f"Session ID: {session_id}")
            print(f"Message: {message}")
            print(f"PDF file received: {pdf_file.name if pdf_file else 'None'}")
            
            if not session_id or not pdf_file:
                print("Missing session_id or file")
                return JsonResponse({'error': 'Missing session_id or file'}, status=400)
            
            # Get the session
            try:
                session = ChatSession.objects.get(id=session_id)
                print(f"Session found: {session.id}")
            except ChatSession.DoesNotExist:
                print(f"Invalid session ID: {session_id}")
                return JsonResponse({'error': 'Invalid session ID'}, status=400)
            
            # Extract text from PDF
            print("Extracting text from PDF...")
            pdf_text = extract_text_from_pdf(pdf_file)
            pdf_name = pdf_file.name
            print(f"Extracted {len(pdf_text)} characters from PDF")
            
            # Store user message if provided
            if message:
                ChatMessage.objects.create(
                    session=session,
                    is_bot=False,
                    content=f"I've uploaded a PDF document: {pdf_name}. {message}"
                )
                print("User message with PDF stored")
            else:
                ChatMessage.objects.create(
                    session=session,
                    is_bot=False,
                    content=f"I've uploaded a PDF document: {pdf_name}"
                )
                print("PDF upload message stored")
            
            # Create a prompt for Gemini based on extracted text
            # Limit text length if necessary to avoid exceeding token limits
            max_text_length = 15000  # Adjust based on model limitations
            trimmed_text = pdf_text[:max_text_length] + ("..." if len(pdf_text) > max_text_length else "")
            
            # Default prompt if no specific message is provided
            if not message:
                prompt = f"""I've uploaded a PDF document named '{pdf_name}'. Here's the extracted text:

{trimmed_text}

Please provide:
1. A concise summary of the key points
2. Important notes/takeaways
3. 3-5 questions that this document answers
"""
            else:
                # If user has a specific question about the document
                prompt = f"""I've uploaded a PDF document named '{pdf_name}'. Here's the extracted text:

{trimmed_text}

User request: {message}
"""
            
            print("Getting response from Gemini...")
            # Get response from Gemini
            response = get_response(prompt, session)
            print(f"Received response of length {len(response)}")
            
            # Store bot response
            ChatMessage.objects.create(
                session=session,
                is_bot=True,
                content=response
            )
            print("Bot response stored")
            
            return JsonResponse({
                'message': response,
                'session_id': session_id
            })
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def get_sessions(request):
    """Get list of chat sessions"""
    try:
        # Get all sessions (or limit to recent ones)
        sessions = ChatSession.objects.all().order_by('-created_at')[:10]
       
        # Format sessions for response
        sessions_list = []
        for session in sessions:
            sessions_list.append({
                'id': str(session.id),
                'title': session.title or "Untitled Chat",
                'created_at': session.created_at.isoformat()
            })
       
        # IMPORTANT FIX: Return a properly formatted response with 'sessions' key
        return JsonResponse({'sessions': sessions_list}, safe=False)
    except Exception as e:
        print(f"Error getting sessions: {str(e)}")
        traceback.print_exc()
        # Return empty array instead of error object to prevent forEach error
        return JsonResponse({'sessions': []}, safe=False)


@csrf_exempt
def get_session(request, session_id):
    """Get session details and messages"""
    try:
        # Find the session by ID
        session = ChatSession.objects.get(id=session_id)
        
        # Get all messages for this session, ordered by creation time
        messages = []
        for msg in ChatMessage.objects.filter(session=session).order_by('created_at'):
            # Convert is_bot to role format expected by frontend
            role = 'bot' if msg.is_bot else 'user'
            messages.append({
                'role': role,
                'content': msg.content,
                'timestamp': msg.created_at.isoformat() if hasattr(msg, 'created_at') else None
            })
        
        # Format session data for response
        session_data = {
            'session_id': str(session.id),
            'title': session.title or "Untitled Chat",
            'created_at': session.created_at.isoformat() if hasattr(session, 'created_at') else None,
            'updated_at': session.updated_at.isoformat() if hasattr(session, 'updated_at') else None,
            'messages': messages
        }
        
        # Add user info if available and session is associated with a user
        if hasattr(session, 'user') and session.user:
            session_data['user'] = {
                'id': session.user.id,
                'username': session.user.username
            }
        
        return JsonResponse(session_data)
    
    except ChatSession.DoesNotExist:
        return JsonResponse({'error': 'Session not found'}, status=404)
    
    except Exception as e:
        print(f"Error getting session {session_id}: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def delete_session(request, session_id):
    """Delete a chat session"""
    if request.method == 'DELETE':
        try:
            # Find the session
            session = ChatSession.objects.get(id=session_id)
            
            # Delete all messages in the session
            ChatMessage.objects.filter(session=session).delete()
            
            # Delete the session
            session.delete()
            
            return JsonResponse({'success': True})
        except ChatSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
        except Exception as e:
            print(f"Error deleting session: {str(e)}")
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def message(request):
    """Alternative name for process_message function"""
    return process_message(request)


def message_view(request):
    """Handles chatbot API messages with validation and error handling"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("Received data:", data)  # Print the received data
           
            # Log all required fields
            message = data.get('message')
            session_id = data.get('session_id')
            print(f"Message: {message}, Session ID: {session_id}")
           
            # Validate required fields
            if not message or not session_id:
                return JsonResponse({'error': 'Missing required fields'}, status=400)
               
            # Get or create session - FIXED to use id instead of session_id
            try:
                session = ChatSession.objects.get(id=session_id)
            except ChatSession.DoesNotExist:
                # Create a new session if it doesn't exist
                session = ChatSession.objects.create()
                session_id = str(session.id)  # Get the new UUID as string
                welcome_message = "Hello, This is Engineering Hub how can I help you today?"
                ChatMessage.objects.create(
                    session=session, 
                    is_bot=True,  # FIXED: using is_bot instead of role
                    content=welcome_message
                )
           
            # Store user message - FIXED to use is_bot instead of role
            ChatMessage.objects.create(
                session=session,
                is_bot=False,  # FIXED: User message, so is_bot=False
                content=message
            )
           
            # Generate response (using our existing logic)
            response = generate_response(message, session)
           
            # Store bot response - FIXED to use is_bot instead of role
            ChatMessage.objects.create(
                session=session,
                is_bot=True,  # FIXED: Bot message, so is_bot=True
                content=response
            )
           
            return JsonResponse({'response': response})
           
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f"Error in message_view: {str(e)}")
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)
   
    # For GET requests, render the chat interface
    return render(request, 'chatbot/chatbot.html')


def chat_interface(request):
    """Render the chat interface page"""
    return render(request, 'chatbot/chatbot.html')


def chatbot_api_docs(request):
    """Render the API documentation page"""
    return render(request, 'chatbot/api_docs.html')

def test_handwritten_pdf(pdf_file):
    """Process a handwritten PDF file using OCR"""
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            for chunk in pdf_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name
            
        # Convert PDF to images
        images = convert_from_path(temp_file_path)
        
        # Process each page with Tesseract OCR
        text = ""
        for i, image in enumerate(images):
            page_text = pytesseract.image_to_string(image)
            text += f"--- Page {i+1} ---\n{page_text}\n\n"
        
        # Delete temporary file
        os.unlink(temp_file_path)
        
        return text
    except Exception as e:
        print(f"Error processing handwritten PDF: {str(e)}")
        return f"Error processing PDF: {str(e)}"

def test_handwritten_form(form_file):
    """Process a handwritten form using OCR"""
    try:
        # Determine file type
        if form_file.name.lower().endswith('.pdf'):
            # Handle as PDF
            return test_handwritten_pdf(form_file)
        else:
            # Handle as image
            return test_handwritten_image(form_file)
    except Exception as e:
        print(f"Error processing handwritten form: {str(e)}")
        return f"Error processing form: {str(e)}"

def attempt_typo_correction(query):
    """
    Attempt to correct typos in the query by comparing with known terms
    """
    try:
        from difflib import get_close_matches
        
        # List of known terms from your database
        # This should be cached or loaded once for performance
        known_terms = []
        
        # Get all resource titles and convert to lowercase
        for title in Resource.objects.values_list('title', flat=True).distinct():
            known_terms.extend(title.lower().split())
        
        # Get all department names
        for dept in Department.objects.values_list('name', flat=True).distinct():
            known_terms.append(dept.lower())
        
        # Add common engineering terms
        common_terms = [
            'communication', 'system', 'digital', 'electronics', 'analog',
            'computer', 'networks', 'data', 'structures', 'algorithms',
            'operating', 'database', 'software', 'engineering', 'artificial',
            'intelligence', 'machine', 'learning', 'control', 'signal',
            'processing', 'power', 'microprocessor', 'architecture',
            'embedded', 'vlsi', 'wireless', 'antenna', 'electromagnetic',
            'circuit', 'theory', 'electrical', 'machines', 'thermodynamics',
            'fluid', 'mechanics', 'strength', 'materials', 'manufacturing',
            'drawing', 'mathematics', 'physics', 'chemistry', 'syllabus',
            'notes', 'handwritten', 'insight', 'lecture'
        ]
        known_terms.extend(common_terms)
        
        # Remove duplicates
        known_terms = list(set(known_terms))
        
        # Split the query into words
        words = query.lower().split()
        corrected_words = []
        
        for word in words:
            # Skip short words and common words
            if len(word) <= 3 or word in ['the', 'and', 'for', 'of', 'to', 'in', 'is', 'a', 'an']:
                corrected_words.append(word)
                continue
            
            # Find close matches
            matches = get_close_matches(word, known_terms, n=1, cutoff=0.8)
            if matches:
                corrected_words.append(matches[0])
            else:
                corrected_words.append(word)
        
        corrected_query = ' '.join(corrected_words)
        return corrected_query
    
    except Exception as e:
        print(f"Error in typo correction: {str(e)}")
        return query  # Return original query if there's an error


