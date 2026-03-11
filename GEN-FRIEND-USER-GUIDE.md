# Gen-Friend v3 - Complete Feature & User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Onboarding](#onboarding)
3. [Goals Management](#goals-management)
4. [If-Then Plans](#if-then-plans)
5. [Tasks & Daily Planning](#tasks--daily-planning)
6. [Progress Tracking](#progress-tracking)
7. [Journal & Reflection](#journal--reflection)
8. [AI Chat Companion](#ai-chat-companion)
9. [Notifications](#notifications)
10. [Settings & Preferences](#settings--preferences)
11. [Admin Panel](#admin-panel)
12. [API Reference](#api-reference)

---

## Getting Started

### Prerequisites
- Node.js 18+ for frontend
- Python 3.10+ for backend
- PostgreSQL database
- Anthropic API key (for AI features)

### Installation

**Backend:**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
alembic upgrade head
uvicorn app.main:app --reload --port 8001
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with your settings
npm run dev
```

### Environment Variables

**Backend (.env):**
```
DATABASE_URL=postgresql://user:pass@localhost:5432/genfriend
ANTHROPIC_API_KEY=sk-ant-xxx
SECRET_KEY=your-secret-key
ADMIN_SECRET_KEY=your-admin-key
CLERK_SECRET_KEY=your-clerk-key (optional)
```

**Frontend (.env.local):**
```
NEXT_PUBLIC_API_URL=http://localhost:8001/api/v1
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your-key (optional)
```

---

## Onboarding

### URL: `/onboarding`

The onboarding flow personalizes your Gen-Friend experience through 8 steps:

### Steps

1. **Welcome** - Introduction to Gen-Friend
2. **Your Name** - Enter your display name
3. **Coach Name** - Name your AI coach (default: "Gen")
4. **Coach Relationship** - Choose how you relate to your coach:
   - Mentor (Wise guide with experience)
   - Coach (Performance-focused partner)
   - Friend (Casual and relatable)
   - Accountability Partner (Keeps you on track)
5. **Communication Tone** - Select preferred interaction style:
   - Supportive (Encouraging and warm)
   - Direct (Straightforward and clear)
   - Challenging (Pushes you to grow)
   - Analytical (Data-driven insights)
6. **Notifications** - Enable daily reminders and weekly summaries
7. **Quiet Hours** - Set do-not-disturb times (e.g., 10 PM - 7 AM)
8. **Complete** - Setup confirmation

### How to Use
1. Navigate to `/onboarding`
2. Click "Let's Go" on welcome screen
3. Complete each step by providing information and clicking "Continue"
4. Your preferences are saved automatically upon completion

---

## Goals Management

### URL: `/goals`

### Creating a Goal (WOOP Wizard)

**URL:** `/goals/new`

Gen-Friend uses the scientifically-backed WOOP framework for goal creation:

1. **Future You** - Describe your ideal future self
   - "How would the successful version of you describe your life?"

2. **Wish** - Define your specific goal
   - "What ONE thing would move you closer to that future?"
   - Example: "Learn to speak Spanish fluently"

3. **Outcome** - Visualize success
   - "What will it look like when you achieve this?"
   - "How will you feel?"

4. **Obstacle** - Identify potential barriers
   - Select from common obstacles:
     - Time/Schedule conflicts
     - Motivation/Energy
     - Distractions/Focus
     - Fear/Self-doubt
     - Resources/Tools
     - Other commitments
     - Perfectionism
     - Procrastination

5. **Plan** - Create If-Then plans
   - "IF [obstacle occurs], THEN I will [specific action]"
   - Example: "IF I feel too tired, THEN I'll do just 5 minutes of practice"

6. **Review** - Confirm your goal details
   - Set timeframe (7 days to 90 days)
   - Choose goal type (career, skill, income, health, personal)

### Endowed Progress Feature

Goals start at 20% progress (not 0%) based on psychological research showing this increases completion rates. The system recognizes your existing effort and knowledge.

### Goal Actions

| Action | How to Do It |
|--------|--------------|
| View Goals | Navigate to `/goals` |
| Create Goal | Click "Create Goal" button |
| View Details | Click on any goal card |
| Update Progress | Use progress slider on goal detail page |
| Pause Goal | Click "Pause" and provide reason |
| Resume Goal | Click "Resume" on paused goal |
| Complete Goal | Mark as complete, record learnings |
| Archive Goal | Archive abandoned goals with reason |
| Delete Goal | Delete from archived goals |

---

## If-Then Plans

### URL: `/goals/[id]/if-then`

If-Then Plans (Implementation Intentions) increase goal success by 2-3x according to research.

### Structure

```
WHEN [trigger situation], THEN I will [specific action]
```

### Examples

| Obstacle | If-Then Plan |
|----------|--------------|
| Time constraints | WHEN I have only 10 minutes, THEN I'll do one small task |
| Low motivation | WHEN I don't feel like it, THEN I'll commit to just 2 minutes |
| Distractions | WHEN I get distracted, THEN I'll close all tabs and refocus |
| Procrastination | WHEN I want to delay, THEN I'll start with the easiest part |

### Managing If-Then Plans

1. Navigate to a goal's If-Then page: `/goals/[goal-id]/if-then`
2. **Add Plan:** Click "Add If-Then Plan" button
3. **Set Primary:** Mark your most important plan as primary
4. **Log Usage:** After encountering an obstacle, record:
   - "Used & Effective" - Plan worked well
   - "Used but Struggled" - Plan needs adjustment
   - "Didn't Use" - Need more practice
5. **View Stats:** Click "View Effectiveness" to see success rates

---

## Tasks & Daily Planning

### URL: `/tasks`

### Creating Tasks

1. Click "+ Add Task" button
2. Enter task title
3. Optionally link to a goal
4. Set scheduled date
5. Click "Create"

### Task States

| State | Description |
|-------|-------------|
| Pending | Not yet started |
| In Progress | Currently working on |
| Completed | Finished |

### Daily Planning

Navigate to `/planning` for AI-generated daily plans including:
- Career tasks
- Skill development activities
- Income-building actions

---

## Progress Tracking

### Multi-Dimensional Progress

Gen-Friend tracks progress across multiple dimensions:

1. **Effort Score** (0-100)
   - Days engaged this week
   - Time invested
   - If-Then plan triggers

2. **Consistency Score** (0-100)
   - Current streak
   - Total active days
   - Weekly rhythm percentage

3. **Completion Score** (0-100)
   - Tasks completed
   - Completion rate percentage

4. **Momentum Score** (0-100)
   - Velocity (rate of progress)
   - Trend (accelerating/steady/slowing)

### Leading Indicators

Track daily behaviors that predict success:
- **Showed Up** - Did you engage with your goal today?
- **Task Attempted** - Did you try to complete a task?
- **If-Then Triggered** - Did an obstacle occur?
- **If-Then Used** - Did you use your plan?
- **Time Invested** - Minutes spent on goal

### Streak Resilience

Unlike fragile consecutive day streaks:
- **Total Active Days** - Cumulative days worked (never lost)
- **Freeze Days** - Protect your streak (earned through consistency)
- **Recovery Count** - How many times you bounced back

### Viewing Progress

1. Navigate to `/goals/[id]`
2. View progress dashboard showing all dimensions
3. Click "Analysis" for detailed breakdown
4. Check "Leading Indicators" tab for daily metrics

---

## Journal & Reflection

### URL: `/journal`

### Entry Types

| Type | Purpose |
|------|---------|
| Reflection | Daily thoughts and learnings |
| Win | Celebrate achievements |
| Challenge | Document obstacles faced |
| Insight | Record realizations |
| Gratitude | Note what you're thankful for |

### Creating Entries

1. Navigate to `/journal`
2. Click "New Entry"
3. Select entry type
4. Write your content
5. Optionally link to a goal
6. Set mood (positive/neutral/challenging)
7. Click "Save"

### Weekly Reflection

**URL:** `/reflection`

Every week, complete a structured reflection:

1. **What went well** - List your wins
2. **Challenges faced** - Document obstacles
3. **What you learned** - Record insights
4. **Next week focus** - Set priorities
5. **Energy level** (1-5)
6. **Satisfaction level** (1-5)

---

## AI Chat Companion

### URL: `/chat`

Your personalized AI coach for career and skill development.

### Capabilities

- Career advice and planning
- Skill development guidance
- Daily task suggestions
- Motivation and encouragement
- Goal strategy discussions
- Obstacle problem-solving

### Boundaries

Gen-Friend focuses ONLY on:
- Career planning and job search
- Skill development
- Daily productivity
- Income/business building

It does NOT provide advice on:
- Health/medical topics
- Mental health/therapy
- Relationships/dating
- Detailed financial/banking

### How to Use

1. Navigate to `/chat`
2. Type your question or concern
3. Receive personalized AI response
4. Continue conversation for follow-up

---

## Notifications

### URL: `/notifications`

### Notification Types

| Type | Icon | Description |
|------|------|-------------|
| Reminder | Clock | Task and goal reminders |
| Insight | Lightbulb | AI-generated observations |
| Motivation | Bell | Encouragement messages |
| Milestone | Target | Achievement celebrations |
| Warning | Bell (red) | Goals at risk alerts |

### Managing Notifications

1. View all notifications at `/notifications`
2. Mark individual notifications as read
3. Dismiss notifications you've addressed
4. Click "Settings" to configure preferences

### Notification Settings

- **Daily Reminders** - Morning task notifications
- **Weekly Summary** - End-of-week progress report
- **Milestone Alerts** - Achievement celebrations
- **Insight Notifications** - AI pattern observations
- **Quiet Hours** - No notifications during set times

---

## Settings & Preferences

### URL: `/settings`

### Profile Settings

- Update your display name
- View your email (cannot be changed)

### Coach Settings

Personalize your AI companion:

| Setting | Options |
|---------|---------|
| Coach Name | Any name you prefer |
| Tone | Supportive, Direct, Challenging, Analytical |
| Relationship | Mentor, Coach, Friend, Accountability Partner |

### Notification Settings

- Toggle daily reminders
- Toggle weekly summary
- Toggle milestone alerts
- Toggle insight notifications
- Set quiet hours (start/end time)

### Appearance Settings

- Dark mode toggle
- Compact view toggle

### Privacy Settings

- Data collection consent
- Anonymized data sharing for AI improvement

### Account Actions

| Action | Description |
|--------|-------------|
| Export Data | Download all your data as JSON (GDPR compliant) |
| Delete Account | Permanently remove account and all data |
| Sign Out | Log out of current session |

---

## Admin Panel

### URL: `/admin`

**Note:** Requires admin secret key to access.

### Authentication

1. Navigate to `/admin`
2. Enter your admin secret key
3. Click "Access Admin"

### Features

#### User Management

| Action | Description |
|--------|-------------|
| List Users | View all users with search |
| View User | See user details, goals, and stats |
| Reset User | Reset specific user data (goals, onboarding, streaks, or all) |
| Delete User | Permanently remove user and all data |

#### System Statistics

- Total users count
- Active users (last 7 days)
- Total goals created
- Total tasks completed

### Reset Options

| Type | What It Resets |
|------|----------------|
| All | Everything - full account reset |
| Goals | All goals, tasks, and progress |
| Onboarding | User preferences and profile |
| Streaks | Streak data only |

---

## API Reference

### Base URL

```
http://localhost:8001/api/v1
```

### Authentication

All endpoints require Bearer token authentication:
```
Authorization: Bearer <token>
```

### Endpoints Summary

#### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Create account |
| POST | `/auth/login` | Get access token |

#### Identity
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/identity` | Get user identity |
| POST | `/identity` | Create identity |
| POST | `/identity/refine` | Update identity |

#### Goals
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/goals` | List all goals |
| POST | `/goals` | Create goal |
| GET | `/goals/{id}` | Get goal details |
| PATCH | `/goals/{id}` | Update goal |
| DELETE | `/goals/{id}` | Delete goal |
| POST | `/goals/{id}/pause` | Pause goal |
| POST | `/goals/{id}/resume` | Resume goal |
| POST | `/goals/{id}/complete` | Complete goal |
| POST | `/goals/{id}/archive` | Archive goal |
| POST | `/goals/{id}/restore` | Restore goal |

#### If-Then Plans
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/if-then/goals/{id}/plans` | Get plans for goal |
| POST | `/if-then/goals/{id}/plans` | Create plan |
| PATCH | `/if-then/plans/{id}` | Update plan |
| DELETE | `/if-then/plans/{id}` | Delete plan |
| POST | `/if-then/plans/{id}/log` | Log plan usage |
| GET | `/if-then/plans/{id}/effectiveness` | Get effectiveness stats |

#### Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tasks` | List tasks |
| POST | `/tasks` | Create task |
| PATCH | `/tasks/{id}` | Update task |
| POST | `/tasks/{id}/complete` | Complete task |
| DELETE | `/tasks/{id}` | Delete task |

#### Progress
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/progress/overview` | Get progress overview |
| GET | `/progress/patterns` | Get detected patterns |
| POST | `/progress/detect-patterns` | Run pattern detection |
| GET | `/progress/goals/{id}/analysis` | Get goal analysis |
| GET | `/progress/goals/{id}/leading-indicators` | Get leading indicators |
| POST | `/progress/goals/{id}/leading-indicators` | Log indicators |
| POST | `/progress/goals/{id}/streak/use-freeze` | Use freeze day |
| GET | `/progress/goals/{id}/streak/history` | Get streak history |

#### Journal
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/journal` | List entries |
| POST | `/journal` | Create entry |
| GET | `/journal/wins` | Get win entries |
| POST | `/journal/recall` | AI-powered recall |

#### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Send message |
| GET | `/chat/history` | Get chat history |

#### Planning
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/planning/today` | Get today's plan |
| POST | `/planning/today` | Generate plan |
| GET | `/planning/weekly-review` | Get weekly review |

#### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users/me` | Get current user |
| DELETE | `/users/me` | Delete account |
| GET | `/users/me/export` | Export all data |

#### Preferences
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/preferences` | Get preferences |
| PATCH | `/preferences` | Update preferences |

#### Admin (requires admin_key)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/users` | List all users |
| GET | `/admin/users/{id}` | Get user details |
| DELETE | `/admin/users/{id}` | Delete user |
| POST | `/admin/users/{id}/reset` | Reset user data |
| GET | `/admin/stats` | Get system stats |

---

## Best Practices

### For Users

1. **Complete onboarding** - Personalization improves AI coaching quality
2. **Create WOOP goals** - Use the full wizard for better success rates
3. **Add If-Then plans** - 2-3 plans per goal dramatically increases success
4. **Log daily indicators** - Track "showing up" not just completion
5. **Weekly reflection** - Review progress every week
6. **Use freeze days wisely** - Protect streaks during difficult periods
7. **Chat regularly** - The AI learns and adapts to your needs

### For Admins

1. **Secure admin key** - Use strong, unique admin secret
2. **Regular backups** - Export user data regularly
3. **Monitor stats** - Track engagement trends
4. **Handle resets carefully** - Confirm before resetting user data
5. **GDPR compliance** - Honor data export/deletion requests promptly

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Login fails | Check Clerk configuration or use dev mode |
| API errors | Verify backend is running on port 8001 |
| No AI responses | Check ANTHROPIC_API_KEY in .env |
| Database errors | Run `alembic upgrade head` |
| 401 Unauthorized | Token expired, re-login |
| Goals not loading | Check user has completed onboarding |

### Development Mode

For local testing without Clerk:
1. Set `NEXT_PUBLIC_DEV_MODE=true` in frontend
2. System will use mock authentication
3. All API calls bypass Clerk verification

---

## Support

For issues and feature requests:
- GitHub Issues: Report bugs and suggest features
- Documentation: Check this guide and API docs
- Chat: Ask the AI companion for help with the app

---

*Gen-Friend v3 - Your AI-Powered Goal Achievement Companion*
