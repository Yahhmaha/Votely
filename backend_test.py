import requests
import json
import time
import random
import string
from pprint import pprint

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL'):
            BACKEND_URL = line.split('=')[1].strip()
            break

API_URL = f"{BACKEND_URL}/api"
print(f"Testing API at: {API_URL}")

# Test users
test_users = []
test_polls = []

def random_string(length=8):
    """Generate a random string for test data"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def create_test_user():
    """Create a test user and return the user data"""
    username = f"testuser_{random_string()}"
    email = f"{username}@example.com"
    password = "Password123!"
    
    user_data = {
        "username": username,
        "email": email,
        "password": password
    }
    
    return user_data

def test_user_registration():
    """Test user registration endpoint"""
    print("\n=== Testing User Registration ===")
    
    # Test with valid data
    user_data = create_test_user()
    response = requests.post(f"{API_URL}/register", json=user_data)
    
    if response.status_code == 200:
        print(f"✅ User registration successful: {user_data['username']}")
        user_profile = response.json()
        test_users.append({**user_data, "id": user_profile["id"]})
        return user_profile
    else:
        print(f"❌ User registration failed: {response.status_code}")
        print(response.text)
        return None

def test_user_login(valid=True):
    """Test user login endpoint"""
    print("\n=== Testing User Login ===")
    
    if not test_users:
        print("No test users available. Creating one...")
        test_user_registration()
    
    user = test_users[0]
    
    login_data = {
        "email": user["email"],
        "password": "WrongPassword123!" if not valid else user["password"]
    }
    
    response = requests.post(f"{API_URL}/login", json=login_data)
    
    if valid:
        if response.status_code == 200:
            print(f"✅ User login successful: {user['username']}")
            return response.json()
        else:
            print(f"❌ User login failed (expected success): {response.status_code}")
            print(response.text)
            return None
    else:
        if response.status_code != 200:
            print(f"✅ Invalid login correctly rejected: {response.status_code}")
            return None
        else:
            print(f"❌ Invalid login incorrectly accepted")
            return response.json()

def test_poll_creation(user_id=None):
    """Test poll creation endpoint"""
    print("\n=== Testing Poll Creation ===")
    
    if not user_id and test_users:
        user_id = test_users[0]["id"]
    
    if not user_id:
        print("No user ID available. Creating a test user...")
        user_profile = test_user_registration()
        if user_profile:
            user_id = user_profile["id"]
        else:
            print("Failed to create test user")
            return None
    
    poll_data = {
        "title": f"Test Poll {random_string()}",
        "description": f"This is a test poll created at {time.time()}",
        "options": [f"Option {i+1}" for i in range(4)],
        "tags": ["test", "automated"]
    }
    
    response = requests.post(f"{API_URL}/polls?user_id={user_id}", json=poll_data)
    
    if response.status_code == 200:
        print(f"✅ Poll creation successful: {poll_data['title']}")
        poll = response.json()
        test_polls.append(poll)
        return poll
    else:
        print(f"❌ Poll creation failed: {response.status_code}")
        print(response.text)
        return None

def test_get_polls():
    """Test retrieving all polls"""
    print("\n=== Testing Get All Polls ===")
    
    response = requests.get(f"{API_URL}/polls")
    
    if response.status_code == 200:
        polls = response.json()
        print(f"✅ Retrieved {len(polls)} polls successfully")
        return polls
    else:
        print(f"❌ Failed to retrieve polls: {response.status_code}")
        print(response.text)
        return None

def test_get_poll_by_id(poll_id=None):
    """Test retrieving a specific poll by ID"""
    print("\n=== Testing Get Poll by ID ===")
    
    if not poll_id and test_polls:
        poll_id = test_polls[0]["id"]
    
    if not poll_id:
        print("No poll ID available. Creating a test poll...")
        poll = test_poll_creation()
        if poll:
            poll_id = poll["id"]
        else:
            print("Failed to create test poll")
            return None
    
    response = requests.get(f"{API_URL}/polls/{poll_id}")
    
    if response.status_code == 200:
        poll = response.json()
        print(f"✅ Retrieved poll successfully: {poll['title']}")
        return poll
    else:
        print(f"❌ Failed to retrieve poll: {response.status_code}")
        print(response.text)
        return None

def test_vote_on_poll(user_id=None, poll_id=None, option_index=0):
    """Test voting on a poll"""
    print("\n=== Testing Vote on Poll ===")
    
    if not user_id and test_users:
        user_id = test_users[0]["id"]
    
    if not user_id:
        print("No user ID available. Creating a test user...")
        user_profile = test_user_registration()
        if user_profile:
            user_id = user_profile["id"]
        else:
            print("Failed to create test user")
            return None
    
    if not poll_id and test_polls:
        poll_id = test_polls[0]["id"]
    
    if not poll_id:
        print("No poll ID available. Creating a test poll...")
        poll = test_poll_creation(user_id)
        if poll:
            poll_id = poll["id"]
        else:
            print("Failed to create test poll")
            return None
    
    # Get the poll to find an option ID
    poll = test_get_poll_by_id(poll_id)
    if not poll:
        print("Failed to retrieve poll")
        return None
    
    if option_index >= len(poll["options"]):
        option_index = 0
    
    option_id = poll["options"][option_index]["id"]
    
    vote_data = {
        "poll_id": poll_id,
        "option_id": option_id,
        "user_id": user_id
    }
    
    response = requests.post(f"{API_URL}/vote", json=vote_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Vote recorded successfully. Total votes: {result['total_votes']}")
        return result
    else:
        print(f"❌ Failed to vote: {response.status_code}")
        print(response.text)
        return None

def test_duplicate_vote(user_id=None, poll_id=None):
    """Test preventing duplicate votes from the same user"""
    print("\n=== Testing Duplicate Vote Prevention ===")
    
    # First vote should succeed
    result = test_vote_on_poll(user_id, poll_id)
    if not result:
        print("First vote failed, cannot test duplicate prevention")
        return None
    
    # Second vote should fail
    if not user_id and test_users:
        user_id = test_users[0]["id"]
    
    if not poll_id and test_polls:
        poll_id = test_polls[0]["id"]
    
    # Get the poll to find an option ID
    poll = test_get_poll_by_id(poll_id)
    if not poll:
        print("Failed to retrieve poll")
        return None
    
    option_id = poll["options"][0]["id"]
    
    vote_data = {
        "poll_id": poll_id,
        "option_id": option_id,
        "user_id": user_id
    }
    
    response = requests.post(f"{API_URL}/vote", json=vote_data)
    
    if response.status_code != 200:
        print(f"✅ Duplicate vote correctly rejected: {response.status_code}")
        return True
    else:
        print(f"❌ Duplicate vote incorrectly accepted")
        return False

def test_get_leaderboard():
    """Test leaderboard endpoint"""
    print("\n=== Testing Leaderboard ===")
    
    response = requests.get(f"{API_URL}/leaderboard")
    
    if response.status_code == 200:
        leaderboard = response.json()
        print(f"✅ Retrieved leaderboard with {len(leaderboard)} users")
        return leaderboard
    else:
        print(f"❌ Failed to retrieve leaderboard: {response.status_code}")
        print(response.text)
        return None

def test_get_user_profile(user_id=None):
    """Test user profile retrieval"""
    print("\n=== Testing User Profile Retrieval ===")
    
    if not user_id and test_users:
        user_id = test_users[0]["id"]
    
    if not user_id:
        print("No user ID available. Creating a test user...")
        user_profile = test_user_registration()
        if user_profile:
            user_id = user_profile["id"]
        else:
            print("Failed to create test user")
            return None
    
    response = requests.get(f"{API_URL}/users/{user_id}/profile")
    
    if response.status_code == 200:
        profile = response.json()
        print(f"✅ Retrieved user profile successfully: {profile['username']}")
        return profile
    else:
        print(f"❌ Failed to retrieve user profile: {response.status_code}")
        print(response.text)
        return None

def test_get_user_achievements(user_id=None):
    """Test user achievements retrieval"""
    print("\n=== Testing User Achievements Retrieval ===")
    
    if not user_id and test_users:
        user_id = test_users[0]["id"]
    
    if not user_id:
        print("No user ID available. Creating a test user...")
        user_profile = test_user_registration()
        if user_profile:
            user_id = user_profile["id"]
        else:
            print("Failed to create test user")
            return None
    
    response = requests.get(f"{API_URL}/users/{user_id}/achievements")
    
    if response.status_code == 200:
        achievements = response.json()
        print(f"✅ Retrieved {len(achievements)} user achievements")
        return achievements
    else:
        print(f"❌ Failed to retrieve user achievements: {response.status_code}")
        print(response.text)
        return None

def test_xp_for_poll_creation():
    """Test XP award for poll creation (20 XP)"""
    print("\n=== Testing XP Award for Poll Creation ===")
    
    # Create a new user
    user_profile = test_user_registration()
    if not user_profile:
        print("Failed to create test user")
        return False
    
    user_id = user_profile["id"]
    initial_xp = user_profile["xp"]
    
    # Create a poll
    poll = test_poll_creation(user_id)
    if not poll:
        print("Failed to create test poll")
        return False
    
    # Check user profile for updated XP
    updated_profile = test_get_user_profile(user_id)
    if not updated_profile:
        print("Failed to retrieve updated user profile")
        return False
    
    xp_gained = updated_profile["xp"] - initial_xp
    if xp_gained == 20:
        print(f"✅ User gained 20 XP for poll creation (from {initial_xp} to {updated_profile['xp']})")
        return True
    else:
        print(f"❌ User gained {xp_gained} XP instead of 20 XP for poll creation")
        return False

def test_xp_for_voting():
    """Test XP award for voting (5 XP)"""
    print("\n=== Testing XP Award for Voting ===")
    
    # Create a new user
    user_profile = test_user_registration()
    if not user_profile:
        print("Failed to create test user")
        return False
    
    user_id = user_profile["id"]
    initial_xp = user_profile["xp"]
    
    # Create a poll with another user
    poll_creator = test_user_registration()
    if not poll_creator:
        print("Failed to create poll creator")
        return False
    
    poll = test_poll_creation(poll_creator["id"])
    if not poll:
        print("Failed to create test poll")
        return False
    
    # Vote on the poll
    vote_result = test_vote_on_poll(user_id, poll["id"])
    if not vote_result:
        print("Failed to vote on poll")
        return False
    
    # Check user profile for updated XP
    updated_profile = test_get_user_profile(user_id)
    if not updated_profile:
        print("Failed to retrieve updated user profile")
        return False
    
    xp_gained = updated_profile["xp"] - initial_xp
    if xp_gained == 5:
        print(f"✅ User gained 5 XP for voting (from {initial_xp} to {updated_profile['xp']})")
        return True
    else:
        print(f"❌ User gained {xp_gained} XP instead of 5 XP for voting")
        return False

def test_first_poll_achievement():
    """Test first poll achievement"""
    print("\n=== Testing First Poll Achievement ===")
    
    # Create a new user
    user_profile = test_user_registration()
    if not user_profile:
        print("Failed to create test user")
        return False
    
    user_id = user_profile["id"]
    
    # Create a poll
    poll = test_poll_creation(user_id)
    if not poll:
        print("Failed to create test poll")
        return False
    
    # Check achievements
    achievements = test_get_user_achievements(user_id)
    if not achievements:
        print("Failed to retrieve user achievements")
        return False
    
    first_poll_achievement = next((a for a in achievements if a["title"] == "First Poll Creator"), None)
    if first_poll_achievement:
        print(f"✅ User received 'First Poll Creator' achievement with {first_poll_achievement['xp_bonus']} XP bonus")
        return True
    else:
        print(f"❌ User did not receive 'First Poll Creator' achievement")
        return False

def run_all_tests():
    """Run all tests in sequence"""
    print("\n======= STARTING BACKEND API TESTS =======\n")
    
    # Authentication tests
    user1 = test_user_registration()
    test_user_login(valid=True)
    test_user_login(valid=False)
    
    # Poll management tests
    poll1 = test_poll_creation()
    polls = test_get_polls()
    poll_detail = test_get_poll_by_id()
    
    # Voting system tests
    vote_result = test_vote_on_poll()
    duplicate_prevention = test_duplicate_vote()
    
    # XP and achievement tests
    xp_poll_creation = test_xp_for_poll_creation()
    xp_voting = test_xp_for_voting()
    first_poll = test_first_poll_achievement()
    
    # Leaderboard and profile tests
    leaderboard = test_get_leaderboard()
    user_profile = test_get_user_profile()
    achievements = test_get_user_achievements()
    
    print("\n======= TEST RESULTS SUMMARY =======\n")
    
    print("Authentication:")
    print(f"  - User Registration: {'✅ PASS' if user1 else '❌ FAIL'}")
    print(f"  - Valid Login: {'✅ PASS' if test_user_login(valid=True) else '❌ FAIL'}")
    print(f"  - Invalid Login Rejection: {'✅ PASS' if not test_user_login(valid=False) else '❌ FAIL'}")
    
    print("\nPoll Management:")
    print(f"  - Poll Creation: {'✅ PASS' if poll1 else '❌ FAIL'}")
    print(f"  - Get All Polls: {'✅ PASS' if polls else '❌ FAIL'}")
    print(f"  - Get Poll by ID: {'✅ PASS' if poll_detail else '❌ FAIL'}")
    
    print("\nVoting System:")
    print(f"  - Vote on Poll: {'✅ PASS' if vote_result else '❌ FAIL'}")
    print(f"  - Duplicate Vote Prevention: {'✅ PASS' if duplicate_prevention else '❌ FAIL'}")
    
    print("\nXP and Achievement System:")
    print(f"  - XP for Poll Creation (20 XP): {'✅ PASS' if xp_poll_creation else '❌ FAIL'}")
    print(f"  - XP for Voting (5 XP): {'✅ PASS' if xp_voting else '❌ FAIL'}")
    print(f"  - First Poll Achievement: {'✅ PASS' if first_poll else '❌ FAIL'}")
    
    print("\nLeaderboard and Profile:")
    print(f"  - Leaderboard Retrieval: {'✅ PASS' if leaderboard else '❌ FAIL'}")
    print(f"  - User Profile Retrieval: {'✅ PASS' if user_profile else '❌ FAIL'}")
    print(f"  - User Achievements Retrieval: {'✅ PASS' if achievements else '❌ FAIL'}")

if __name__ == "__main__":
    run_all_tests()