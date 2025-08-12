# Dashboard v5 Setup Guide

**Project Repository:** https://github.com/Cfree1989/Dashboardv5  
**System Password:** Fabrication

---

## 🎯 What You'll Need (Prerequisites)

Before starting, you need to download and install these programs on your computer:

### Required Software
- **Docker Desktop** - Download from [docker.com](https://www.docker.com/products/docker-desktop/)
  - Click the blue "Download Docker Desktop" button
  - Run the installer and follow the setup wizard
  - Restart your computer when prompted
- **Git** - Download from [git-scm.com](https://git-scm.com/)
  - Click "Download for Windows"
  - Run the installer and use all the default options

---

## 🐳 Docker Setup

Docker handles all the complex setup automatically. Just follow these detailed steps:

## Step 1: Open PowerShell

You need to open PowerShell to type commands. Here's how:

**(Windows 11):**
1. Right-click on the Windows Start button (bottom-left corner)
2. Click "Windows PowerShell" or "Terminal" from the menu

You should see a blue window with white text that looks like this:
```
PS C:\Users\YourName>
```

## Step 2: Download and Start the Project

**Important:** Copy and paste these commands one at a time. Don't type them all at once

In the PowerShell window, type (or copy/paste) this command and press Enter:

```powershell
git clone https://github.com/Cfree1989/Dashboardv5 C:\Dashboardv5
```

**What happens:** This downloads your project to your C: drive. You'll see text scrolling as it downloads.

Next, type this command and press Enter:

```powershell
cd C:\Dashboardv5
```

**What happens:** This moves you into the project folder.

Now type this command and press Enter:

```powershell
docker compose up -d --build
```

**What happens:** This starts building and running your dashboard. **This will take several minutes the first time** as Docker downloads and sets up everything. You'll see lots of text scrolling. Don't worry if it seems slow - this is normal!

**Wait for it to finish!** You'll know it's done when you see your cursor back at the command prompt (something like `PS C:\Dashboardv5>`).

## Step 3: Set Up the Database

Still in PowerShell, type this command and press Enter:

```powershell
docker compose exec backend flask db upgrade
```

**What happens:** This creates the database tables your dashboard needs.

Then type this command and press Enter:

```powershell
docker compose exec backend flask seed-data
```

**What happens:** This adds some sample data so you have something to see when you first log in.

## Step 4: Open Your Dashboard

Now the fun part! Open your web browser (Chrome, Firefox, Edge, etc.) and go to these websites:

### Main Dashboard
Type this in your browser's address bar:
```
http://localhost:3000
```

You should see a login screen for your dashboard!

### Health Check (Optional)
To make sure everything is working, you can also check:
```
http://localhost:5000/health
```

This should just show "OK" if everything is running properly.

## Step 5: Log Into Your Dashboard

On the login screen, use these credentials:
- **Workstation:** `front-desk`
- **Password:** `password123`

Click the login button and you should be inside your dashboard!

## Step 6: Managing Your Dashboard

### To Stop the Dashboard
When you're done working and want to stop the dashboard, go back to PowerShell and type:

```powershell
docker compose down
```

**What happens:** This stops all the dashboard services and frees up your computer's resources.

### To Start It Again Later
To start your dashboard again anytime, open PowerShell, then type:

```powershell
cd C:\Dashboardv5
docker compose up -d
```

**Note:** You don't need the `--build` part after the first time.

### If Something Goes Wrong
If you see errors or the dashboard isn't working, type this in PowerShell:

```powershell
docker compose logs backend -f
```

**What happens:** This shows you error messages that can help figure out what's wrong. Press Ctrl+C to stop viewing the logs.

To restart everything fresh:

```powershell
docker compose down
docker compose up -d --build
```

---



## 🧪 Running Tests (Optional)

If you want to test that everything is working correctly, you can run the built-in tests:

```powershell
docker compose exec backend pytest -q
```

**What happens:** This runs automated tests to make sure all parts of your dashboard are working properly.

---

## 📝 Important Notes

### Email Features
- Your dashboard has email features, but they're optional
- If you don't set up email configuration, the system will just skip sending emails
- Everything else will work perfectly without email setup

### Where Files Are Stored
- Any files you upload through the dashboard are saved in a `storage\` folder inside your project
- You can find this folder at `C:\Dashboardv5\storage\`

### Checking If Everything Is Working
- You can always check http://localhost:5000/health in your browser
- If you see "OK", everything is running correctly
- If you see an error or the page won't load, something needs to be restarted

---

## 🆘 Getting Help & Troubleshooting

### If Your Dashboard Won't Load

1. **Check the health page:** Go to http://localhost:5000/health
   - If it shows "OK" → Your backend is working
   - If it won't load → Your backend isn't running

2. **Restart everything:**
   ```powershell
   docker compose down
   docker compose up -d
   ```

3. **Check for errors:**
   ```powershell
   docker compose logs backend -f
   ```
   Press Ctrl+C to stop viewing the logs.

### If You See Port Errors
- Make sure no other programs are using ports 3000 or 5000
- Close other development servers or applications that might be using these ports
- Restart your computer if needed

### If Docker Commands Don't Work
- Make sure Docker Desktop is running (you should see a whale icon in your system tray)
- If Docker Desktop isn't running, click on it from your Start menu

### Common Issues

**"Command not found" errors:**
- Make sure you installed Git and Docker Desktop
- Restart your computer after installation
- Try closing and reopening PowerShell

**Dashboard loads but login doesn't work:**
- Make sure you ran the database setup commands (Step 3)
- Try the seed data command again: `docker compose exec backend flask seed-data`

**Everything seems slow:**
- The first time you run Docker commands, they download a lot of files
- Subsequent startups will be much faster
- This is completely normal!

---

## 🔄 Daily Use

Once you have everything set up, your daily routine will be simple:

### Starting Your Dashboard
1. Open PowerShell
2. Type: `cd C:\Dashboardv5`
3. Type: `docker compose up -d`
4. Open http://localhost:3000 in your browser

### Stopping Your Dashboard
1. In PowerShell, type: `docker compose down`

That's it! The setup is only complicated the first time. After that, it's just two simple commands to start and stop.