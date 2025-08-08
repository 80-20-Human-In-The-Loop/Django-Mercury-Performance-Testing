# 📝 EduLite Technical Writing Standards

> **Clear documentation removes barriers to education. When we write clearly, we make learning accessible to everyone.**

## 🌍 Why Documentation Matters for Global Education

In a project serving students from Palestine to Nigeria, from Sudan to Canada, clear documentation creates real impact:

- **Language Barriers**: Simple writing translates better across 5+ languages
- **Skill Diversity**: Contributors range from teenage students to senior developers
- **Limited Resources**: Clear docs reduce confusion when internet time is precious
- **Educational Impact**: Every confused contributor is one less person helping students

**Our Goal**: Write documentation so clear that a student anywhere with basic English can contribute and learn alongside experienced Senior Developers.

---

## 🎯 Core Writing Principles

### 1. Write for Translation (Think Global)

**Rule**: Every sentence should translate cleanly into Arabic, French, Spanish, and other languages.

**Why it matters**: Our contributors speak dozens of languages. Complex English creates barriers.

#### Guidelines:

```markdown
❌ AVOID: "Let's dive into the nitty-gritty of our cutting-edge features"
✅ USE: "Let's explore the details of our features"

❌ AVOID: "This rocks!" or "It's a piece of cake"
✅ USE: "This works well" or "This is simple"

❌ AVOID: Long, complex sentences with multiple clauses that might confuse readers
✅ USE: Short sentences. One idea per sentence. Clear structure.
```

### 2. Active Voice for Clarity

**Pattern**: [Who] + [Does what] + [To what]

#### EduLite Examples:

```markdown
✅ "Students submit assignments through the platform"
❌ "Assignments are submitted through the platform"

✅ "Teachers create lessons using our tools"
❌ "Lessons are created using our tools"

✅ "The system saves work automatically"
❌ "Work is automatically saved"
```

### 3. Include Everyone (Write for All Skill Levels)

Remember our diverse contributors:
- **Students**: First-time coders
- **Teachers**: May have limited tech experience
- **Developers**: Various experience levels
- **Designers**: Visual thinkers
- **Translators**: Language experts, not necessarily technical

#### Inclusive Writing Patterns:

```markdown
❌ "Just npm install and you're good to go"
✅ "Install the dependencies by running: npm install
   This downloads all the required packages for the project."

❌ "The API endpoint accepts JSON payloads"
✅ "The API endpoint accepts JSON data (structured text format).
   Example: {"name": "Student Name", "grade": 10}"
```

---

## 📚 Writing for Different Audiences

### For Developers

**Focus**: Technical accuracy with human context

```markdown
## User Authentication

**What it does**: Keeps student data safe by verifying identity

**Technical details**:
- Uses JWT tokens (secure digital signatures)
- 24-hour token expiration
- Refresh tokens for extended sessions

**Implementation**:
\```python
# Verify user identity before accessing protected data
@login_required
def view_grades(request):
    # Only authenticated users reach this point
    return render(request, 'grades.html')
\```
```

### For Educators

**Focus**: Educational impact and practical use

```markdown
## Creating Assignments

Teachers can create assignments that work even offline.

**Steps**:
1. Click "New Assignment" in your dashboard
2. Add assignment title and description
3. Set due date (students see this in their timezone)
4. Choose "Allow Offline Work" for students with limited internet

**Why this matters**: Students can download assignments when they have internet,
work offline, and submit when they reconnect.
```

### For Students

**Focus**: Simple steps and clear benefits

```markdown
## Joining a Class

**What you need**: Class code from your teacher

**Steps**:
1. Go to "My Classes"
2. Click "Join Class"
3. Enter the 6-letter code
4. Click "Join"

You're now part of the class! You'll see all assignments and announcements.
```

---

## 🌐 Language & Cultural Considerations

### Simple Word Choices

| ❌ Complex/Idiomatic | ✅ Simple/Clear | Why |
|---------------------|-----------------|-----|
| "Bootstrap the app" | "Start the app" | "Bootstrap" has technical meaning |
| "Leverage our features" | "Use our features" | Simpler verb |
| "Cutting-edge technology" | "Modern technology" | Avoids idioms |
| "Best-in-class" | "High quality" | Clearer meaning |
| "Drill down into" | "Explore" or "Look at details" | Simpler concept |

### Cultural Sensitivity

**Consider global contexts**:

```markdown
❌ "Schedule meetings during business hours (9-5)"
✅ "Schedule meetings at times that work for your timezone"

❌ "Enter your first and last name"
✅ "Enter your name" (naming conventions vary globally)

❌ "Click the hamburger menu"
✅ "Click the menu icon (☰)"
```

### Number and Date Formats

```markdown
❌ "Released on 12/25/2024" (US format)
✅ "Released on December 25, 2024" or "2024-12-25" (ISO format)

❌ "Costs $10.50"
✅ "Costs 10.50 USD" (specify currency)

❌ "1,000 students"
✅ "1000 students" or "1 000 students" (varies by locale)
```

---

## 🔍 Common Patterns

### Error Messages

**Pattern**: [What happened] + [Impact] + [How to fix]

```python
❌ "Error: Invalid data"

✅ "Cannot save assignment. The title is missing. 
    Please add a title and try again."

✅ "Login failed. Email or password incorrect.
    Check your spelling or reset your password."
```

### Feature Descriptions

**Pattern**: [What it does] + [Who benefits] + [How to use]

```markdown
## Offline Mode

**What it does**: Lets students work without internet

**Who benefits**: Students with limited connectivity

**How to use**:
1. Download assignments when online
2. Work offline anytime
3. Your work saves locally
4. When reconnected, it syncs automatically

**Technical note**: Uses IndexedDB for local storage
```

### Step-by-Step Guides

```markdown
## Setting Up Your Development Environment

We'll help you set up EduLite on your computer.

### What you need first:
- Python 3.10 or newer ([Download here](link))
- Git ([Download here](link))
- 2GB free disk space

### Steps:

1. **Get the code**
   ```bash
   git clone https://github.com/ibrahim-sisar/EduLite.git
   cd EduLite
   ```
   This downloads EduLite to your computer

2. **Set up Python environment**
   ```bash
   python -m venv venv
   ```
   This creates an isolated space for EduLite

3. **Activate environment**
   
   Windows:
   ```bash
   venv\Scripts\activate
   ```
   
   Mac/Linux:
   ```bash
   source venv/bin/activate
   ```

[Continue with clear steps...]
```

---

## 🌟 Examples from EduLite

### Good: Clear and Inclusive

```markdown
## Friend Requests

Students can connect with classmates through friend requests.

**How it works**:
1. Search for your classmate by name
2. Click "Add Friend"
3. Wait for them to accept
4. Once connected, you can study together

**Privacy**: Only friends can see your study activity
```

### Needs Improvement:

```markdown
❌ "The UserSerializer leverages Django's ORM to seamlessly integrate with 
    our RESTful API endpoints, providing HATEOAS-compliant responses."

✅ "The UserSerializer formats user data for our API. It converts database 
    records into JSON that applications can read. It also includes links 
    to related data."
```

---

## 🤝 Inclusive Language Guidelines

### Use Welcoming Language

```markdown
❌ "Developers must configure..." (excludes non-developers)
✅ "To set this up, configure..." (anyone can do it)

❌ "Any competent programmer knows..." (gatekeeping)
✅ "Here's how this works..." (welcoming)

❌ "This is trivial to implement" (dismissive)
✅ "This takes just a few steps" (encouraging)
```

### Gender-Neutral Language

```markdown
❌ "The user should update his settings"
✅ "Users should update their settings"
✅ "You should update your settings"
```

### Ability-Inclusive Language

```markdown
❌ "Click the red button"
✅ "Click the 'Submit' button (red)"

❌ "As you can see in the diagram"
✅ "The diagram shows" or "As shown in the diagram"
```

---

## 🔄 Translation Best Practices

### Write for Machine Translation

1. **Use standard terminology**
   - Consistent terms help translation memory
   - Define custom terms clearly

2. **Avoid ambiguity**
   ```markdown
   ❌ "The system will process it"
   ✅ "The system will process the assignment"
   ```

3. **Complete sentences**
   ```markdown
   ❌ "To start: npm install"
   ✅ "To start the application, run: npm install"
   ```

### Translation-Friendly Formatting

```markdown
## Assignment Settings

You can customize each assignment:

**Options**:
- **Due Date**: When students must submit
- **Late Submission**: Allow submissions after due date
- **Offline Mode**: Let students work without internet
- **Auto-Save**: Save student work every 30 seconds

**Note**: These settings apply to all students in the class.
```

---

## 🛠️ Tools and Resources

### Recommended Tools

1. **Hemingway Editor** - Checks readability
2. **Google Translate** - Test translations
3. **Grammarly** - Basic grammar check
4. **Screen readers** - Test accessibility

### Writing Resources

- [Plain Language Guide](https://www.plainlanguage.gov/)
- [Write the Docs](https://www.writethedocs.org/)
- [18F Content Guide](https://content-guide.18f.gov/)

### EduLite-Specific

- Style guide (this document)
- Translation glossary (coming soon)
- Example library (in progress)

---

## 🤲 Getting Help

Writing clearly is hard! Get support:

- **Writing Review**: Post in #documentation on Discord
- **Translation Help**: Ask in #translations
- **Technical Clarity**: Tag a developer for review
- **Educational Context**: Ask our teacher contributors

Remember: **Asking for help makes documentation better for everyone.**

---

## 💫 Remember Our Mission

Every word we write can either:
- **Open doors** for students in Gaza learning to code
- **Build bridges** for teachers in Sudan creating lessons
- **Remove barriers** for developers in Nigeria contributing features

Or it can create obstacles.

**Choose clarity. Choose inclusion. Choose to make education accessible.**

---

*This is a living document maintained by our community. See something that needs improvement? Please contribute!*

> 📚 **When we write for everyone, we build software for everyone. When we build for everyone, we change the world.**