# Recording an iRouter Demo with Asciinema

Step-by-step instructions for recording a professional CLI demo of the Intelligent Query Router.

---

## Prerequisites

### ⚠️ Windows Users: asciinema requires WSL

Asciinema doesn't work on native Windows (it needs Unix PTY support). You have two options:

**Option A: Use WSL (Recommended)**
```bash
# 1. Install WSL if you haven't already (run in PowerShell as Admin)
wsl --install

# 2. Open WSL/Ubuntu terminal
wsl

# 3. Navigate to your project (Windows drives are mounted at /mnt/)
cd /mnt/c/Users/aarus/OneDrive/Desktop/personalprojects/intelligent-query-router

# 4. Install Python and dependencies in WSL
sudo apt update
sudo apt install python3 python3-pip python3-venv
python3 -m venv venv
source venv/bin/activate
pip install -e .

# 5. Install asciinema in WSL
pip install asciinema

# 6. Verify installation
irouter --help
asciinema --version
```

**Option B: Use terminalizer (Windows alternative)**
```bash
# Install Node.js from https://nodejs.org first, then:
npm install -g terminalizer

# Record with terminalizer instead
terminalizer record demo -c "bash ./examples/irouter-demo-short.sh"

# Render to GIF
terminalizer render demo
```

---

### For macOS/Linux Users:

1. **Verify iRouter is installed:**
   ```bash
   cd ~/path/to/intelligent-query-router
   pip install -e .
   irouter --help
   ```

2. **Install asciinema:**
   ```bash
   pip install asciinema
   ```

3. **Generate test data (if not already done):**
   ```bash
   python scripts/generate_test_data.py
   ```

---

## Step-by-Step Recording Instructions

### Step 1: Prepare Your Terminal

```bash
# 1. Open a clean terminal window
# 2. Resize to readable dimensions (recommended: 100 columns x 30 rows)
# 3. Clear any existing output
clear

# 4. Navigate to project directory
cd c:\Users\aarus\OneDrive\Desktop\personalprojects\intelligent-query-router
```

### Step 2: Test Your Demo Script

**Before recording, run through the demo to ensure everything works:**

```bash
# Test the short version (15-30 seconds)
./examples/irouter-demo-short.sh

# OR test the full version (1-2 minutes)
./examples/irouter-demo.sh
```

If you encounter errors, fix them before recording.

### Step 3: Start Recording

**For a quick portfolio demo (recommended):**
```bash
asciinema rec --idle-time-limit 2 -t "iRouter: Intelligent SQL Query Router" irouter-demo.cast
```

**What this does:**
- `rec` - Start recording
- `--idle-time-limit 2` - Automatically trim pauses longer than 2 seconds
- `-t "..."` - Set the title for the recording
- `irouter-demo.cast` - Output filename

### Step 4: Run Your Demo

**Once recording starts, execute your demo script:**

```bash
# For short demo (portfolio/social media)
./examples/irouter-demo-short.sh

# OR for full demo (documentation)
./examples/irouter-demo.sh
```

**Let the script run completely without interruption.**

### Step 5: Stop Recording

When the demo finishes, stop the recording:
```bash
exit
# OR press Ctrl+D
```

### Step 6: Review Your Recording

Play it back to check quality:
```bash
asciinema play irouter-demo.cast
```

**Check for:**
- ✅ All commands executed successfully
- ✅ Output is readable
- ✅ Timing feels natural (not too fast/slow)
- ✅ No errors or typos

**If not satisfied:** Delete the file and go back to Step 3
```bash
del irouter-demo.cast  # Windows
rm irouter-demo.cast   # macOS/Linux
```

### Step 7: Upload (Optional)

**Option A: Upload to asciinema.org**
```bash
asciinema upload irouter-demo.cast
```
You'll get a shareable URL like: `https://asciinema.org/a/abc123`

**Option B: Convert to GIF for README**
```bash
# Install agg converter
cargo install --git https://github.com/asciinema/agg

# Convert to GIF
agg --speed 1.0 --font-size 14 irouter-demo.cast irouter-demo.gif
```

Then embed in README:
```markdown
![iRouter Demo](examples/irouter-demo.gif)
```

**Option C: Keep locally**
Just commit the `.cast` file to your repo:
```bash
git add examples/irouter-demo.cast
git commit -m "Add asciinema demo recording"
```

---

## Quick Recording Checklist

Before you hit record:

- [ ] Terminal is clean and properly sized
- [ ] Test data is generated (`./data` directory exists with sales partitions)
- [ ] Demo script runs without errors
- [ ] iRouter CLI is working (`irouter --help`)
- [ ] You know which demo version to use (short vs. full)
- [ ] Terminal colors/theme is readable

---

## Troubleshooting

**"irouter: command not found"**
```bash
# Make sure you're in the venv and installed the package
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
pip install -e .
```

**Demo script won't run**
```bash
# On Windows with Git Bash
bash ./examples/irouter-demo-short.sh

# Make script executable (macOS/Linux)
chmod +x ./examples/irouter-demo-short.sh
./examples/irouter-demo-short.sh
```

**Recording is too long**
- Use the short version: `./examples/irouter-demo-short.sh`
- Increase `--idle-time-limit` to trim more pauses
- Edit the demo script to reduce sleep times

**Output is hard to read**
- Increase terminal font size before recording
- Use a high-contrast color scheme
- Ensure terminal is at least 100 columns wide

---

## What's in Your Demo Scripts

**Short version** (`irouter-demo-short.sh`) - ~20 seconds
- Single query showing backend selection and partition pruning
- Cache hit demonstration on repeated query
- Performance summary (70-90% fewer files, 100-1000x speedup)
- **Use for:** Portfolio, Twitter/LinkedIn, README

**Full version** (`irouter-demo.sh`) - ~1-2 minutes
- 5 different queries demonstrating:
  1. Simple query → DuckDB selection
  2. Aggregation with execution plan
  3. Partition pruning in action
  4. Cache hit demonstration
  5. Cache statistics
- **Use for:** Documentation, tutorials, GitHub README

---

## Next Steps

After recording:

1. **Review the recording** - Make sure it showcases your best work
2. **Share it** - Upload to asciinema.org or convert to GIF
3. **Update README** - Add the demo link or embed the GIF
4. **Tweet it** - Share with #DataEngineering #SQL hashtags

---

## Example README Embed

**With asciinema.org link:**
```markdown
## Demo

Watch it in action:

[![asciicast](https://asciinema.org/a/abc123.svg)](https://asciinema.org/a/abc123)
```

**With local GIF:**
```markdown
## Demo

![iRouter Demo](examples/irouter-demo.gif)
```

---

## Tips for Best Results

1. **Keep it short** - Attention spans are limited (aim for 15-30 seconds)
2. **Show impact** - Focus on speedup numbers and cache hits
3. **Clean output** - The scripts already handle formatting for you
4. **Test first** - Always run through the script before recording
5. **One take** - Let the script run without pausing/editing

Good luck with your recording! 🎬

## Best Practices

### 1. Prepare Your Environment

**Terminal Setup:**
- Use a clean terminal with standard dimensions (80x24 or 120x30)
- Choose readable color schemes (avoid overly bright/dark themes)
- Set a comfortable font size (14-16pt for recordings)
- Clear terminal history: `clear` or `Ctrl+L`

**Test Your Commands:**
```bash
# Run through your demo script first to catch errors
./irouter-demo.sh

# Make sure all dependencies are installed
which irouter
irouter --version
```

### 2. Recording Settings

**Recommended Command:**
```bash
# Basic recording
asciinema rec demo.cast

# With custom title and environment
asciinema rec -t "iRouter Demo" --env=SHELL demo.cast

# Idle time limit (cuts long pauses to max 2 seconds)
asciinema rec --idle-time-limit 2 demo.cast
```

**Key Parameters:**
- `-t, --title` - Set recording title
- `--idle-time-limit` - Maximum pause duration (e.g., `2` for 2 seconds)
- `--env` - Capture environment variables (use `SHELL,TERM` for basics)
- `-c, --command` - Record specific command instead of shell

### 3. Demo Script Structure

**Good Demo Pattern:**
```bash
#!/bin/bash

# 1. Clear and introduce
clear
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Tool Name: Brief Description"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sleep 1

# 2. Show one feature at a time
echo "# Feature 1: Basic usage"
your-command arg1 arg2
sleep 2

# 3. Build complexity gradually
echo "# Feature 2: Advanced options"
your-command --advanced-flag
sleep 2

# 4. Close with impact
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✓ Key benefit 1"
echo "  ✓ Key benefit 2"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

**Timing Guidelines:**
- **Portfolio/Social Media:** 15-30 seconds (focus on 1-2 key features)
- **Documentation:** 1-2 minutes (show common workflows)
- **Tutorial:** 3-5 minutes (detailed walkthrough)

### 4. Recording Workflow

**Step-by-Step Process:**

1. **Prepare:**
   ```bash
   # Set up clean state
   cd your-project
   clear

   # Optional: resize terminal
   # Most readable: 100 columns x 30 rows
   ```

2. **Start Recording:**
   ```bash
   asciinema rec --idle-time-limit 2 -t "Your Tool Demo" demo.cast
   ```

3. **Run Your Script:**
   ```bash
   # Execute prepared demo script
   ./examples/demo-script.sh

   # OR type commands manually for authenticity
   # (but have them written down!)
   ```

4. **Stop Recording:**
   - Press `Ctrl+D` or type `exit`

5. **Review:**
   ```bash
   asciinema play demo.cast
   # If not satisfied, delete and re-record
   ```

### 5. Common Pitfalls to Avoid

❌ **Don't:**
- Use very long commands without explaining them
- Include typos or command failures (unless demonstrating error handling)
- Let pauses drag on (use `--idle-time-limit`)
- Show sensitive information (API keys, passwords)
- Record in overly customized terminals (others can't replicate the look)

✅ **Do:**
- Add visual separators between sections
- Use echo statements to narrate what's happening
- Keep pacing steady with `sleep` commands
- Show realistic use cases
- End with clear takeaways

### 6. Scripting Tips

**Using Colors:**
```bash
# Define colors at script start
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Use in output
echo -e "${GREEN}✓ Success message${NC}"
echo -e "${YELLOW}[Info] Processing...${NC}"
```

**Controlled Timing:**
```bash
# Variable pause durations
QUICK=1
MEDIUM=2
LONG=3

sleep $QUICK   # Between related commands
sleep $MEDIUM  # Between sections
sleep $LONG    # For important output
```

**Showing Commands Before Running:**
```bash
# Good for tutorial-style demos
echo "$ irouter execute 'SELECT * FROM data'"
sleep 0.5
irouter execute 'SELECT * FROM data'
```

### 7. Post-Recording

**Editing Cast Files:**
Cast files are JSON-based and can be edited:
```bash
# View the cast file
cat demo.cast

# Edit timing manually (advanced)
# Each line: [timestamp, "o", "output"]
# Reduce timestamps to speed up sections
```

**Hosting Options:**
1. **asciinema.org** - Free hosting, embeddable
   ```bash
   asciinema upload demo.cast
   ```

2. **Self-hosted** - Use asciinema-player in HTML
   ```html
   <script src="asciinema-player.js"></script>
   <link rel="stylesheet" href="asciinema-player.css">
   <div id="demo"></div>
   <script>
     AsciinemaPlayer.create('demo.cast', document.getElementById('demo'));
   </script>
   ```

3. **Convert to GIF** (for READMEs)
   ```bash
   # Install agg (faster alternative to asciicast2gif)
   cargo install --git https://github.com/asciinema/agg

   # Convert
   agg demo.cast demo.gif

   # With options
   agg --speed 1.5 --font-size 14 demo.cast demo.gif
   ```

### 8. Example: Two-Version Strategy

**Long Version** (`irouter-demo.sh`) - Full feature showcase (1-2 min)
```bash
# Comprehensive demo showing:
# - Multiple features
# - Different use cases
# - Detailed output
# Target: Documentation, tutorials
```

**Short Version** (`irouter-demo-short.sh`) - Quick highlight (15-30 sec)
```bash
# Focused demo showing:
# - 1-2 killer features
# - Clear before/after or comparison
# - Punchy conclusion
# Target: Social media, portfolio, README
```

## Checklist Before Recording

- [ ] Terminal is clean and properly sized
- [ ] Demo script is tested and working
- [ ] All commands/tools are installed
- [ ] No sensitive data visible
- [ ] Timing feels natural (not too fast/slow)
- [ ] Output is readable at typical sizes
- [ ] You know what you're going to show

## Recording Command Reference

```bash
# Basic recording
asciinema rec output.cast

# With all recommended options
asciinema rec --idle-time-limit 2 \
  -t "Tool Demo" \
  --env=SHELL,TERM \
  output.cast

# Record and immediately upload
asciinema rec --title "Tool Demo" --idle-time-limit 2 output.cast && \
  asciinema upload output.cast

# Append to existing recording
asciinema rec --append output.cast

# Record in overwrite mode (auto-replace on save)
asciinema rec --overwrite output.cast
```

## Resources

- **asciinema docs:** https://docs.asciinema.org/
- **asciinema-player:** https://github.com/asciinema/asciinema-player
- **agg (GIF converter):** https://github.com/asciinema/agg
- **Terminal color codes:** https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797
