# .gitignore Update - User-Specific Files

## Changes Made

Updated `.gitignore` to exclude user-specific settings files from version control.

## Files Now Ignored

### 1. `.cord/last_nick.json`
- **Purpose:** Stores the user's last used nickname
- **Why ignore:** Each user should have their own nickname
- **Created by:** Nickname persistence feature
- **Example content:**
  ```json
  {
    "nick": "alice"
  }
  ```

### 2. `.cord/bookmarks.json`
- **Purpose:** Stores user's bookmarked IRC channels
- **Why ignore:** Each user has different favorite channels
- **Created by:** Bookmark feature
- **Example content:**
  ```json
  {
    "channels": ["#python", "#linux", "#coding"]
  }
  ```

## Why These Files Should Be Ignored

### Personal Preferences
- Nicknames are personal identifiers
- Bookmarks are individual preferences
- Different users = different settings

### Avoid Conflicts
- Multiple developers would overwrite each other's settings
- Git merge conflicts on personal data
- Unnecessary noise in git history

### Privacy
- Nicknames might reveal personal information
- Channel preferences are private
- No need to share with team

## Updated .gitignore Section

```gitignore
# User-specific settings (should not be committed)
.cord/last_nick.json
.cord/bookmarks.json
```

## Migration Steps

If these files are already tracked by git, remove them:

### Option 1: Run the Script
```bash
./update_git_tracking.sh
```

### Option 2: Manual Commands
```bash
# Remove from git tracking (keeps local files)
git rm --cached .cord/last_nick.json
git rm --cached .cord/bookmarks.json

# Commit the change
git commit -m "Update .gitignore for user-specific settings"
```

## What Happens to Existing Files?

### Local Files
- ✅ **Kept** - Your local files remain untouched
- ✅ **Still work** - App continues to use them
- ✅ **Not deleted** - Only removed from git tracking

### Git Repository
- ❌ **Not tracked** - Changes won't be committed
- ❌ **Not pushed** - Won't appear in remote repo
- ❌ **Not pulled** - Won't overwrite others' files

## For New Users

When cloning the repository:
1. These files won't exist initially
2. App will create them on first use
3. They'll be automatically ignored by git
4. Each user gets their own settings

## File Structure

```
.cord/
├── config.json          ← Shared (tracked by git)
├── last_nick.json       ← Personal (ignored) ✓
└── bookmarks.json       ← Personal (ignored) ✓
```

## Benefits

### ✅ Clean Repository
- No personal data in git history
- Smaller repository size
- Cleaner git log

### ✅ No Conflicts
- Each user has their own settings
- No merge conflicts on personal files
- Smooth collaboration

### ✅ Privacy
- Personal preferences stay local
- No accidental sharing of nicknames
- Better security

### ✅ Flexibility
- Users can customize freely
- No fear of committing personal data
- Easy to reset (just delete local file)

## Verification

Check if files are ignored:
```bash
git status
```

Should NOT show:
- `.cord/last_nick.json`
- `.cord/bookmarks.json`

## Troubleshooting

### Files Still Showing in Git Status?

Run the removal script:
```bash
./update_git_tracking.sh
```

Or manually:
```bash
git rm --cached .cord/last_nick.json .cord/bookmarks.json
```

### Want to Track These Files Again?

Remove from .gitignore:
```bash
# Edit .gitignore and remove the lines
git add .cord/last_nick.json .cord/bookmarks.json
git commit -m "Track user settings"
```

(Not recommended for multi-user projects)

## Summary

| File | Purpose | Tracked? | Reason |
|------|---------|----------|--------|
| `config.json` | App configuration | ✅ Yes | Shared settings |
| `last_nick.json` | User's nickname | ❌ No | Personal |
| `bookmarks.json` | User's bookmarks | ❌ No | Personal |

**Result:** Clean repository with proper separation of shared and personal settings! 🎉
