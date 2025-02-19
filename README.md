# Google Forms Auto-Filler

A Python script using Playwright to automatically fill Google Forms containing Multiple Choice Questions (MCQs) with random responses.

## Features

- Automatically fills Google Forms with random selections for MCQ questions
- Runs in non-headless mode (browser window is visible)
- Platform-independent with minimal setup
- Provides real-time progress updates
- Shows submission statistics upon completion
- Utilizes multi-threading to perform parallel submissions leveraging available CPU cores

## Prerequisites

- Python 3.7 or higher

## Installation

1. Clone this repository or download the files
2. Install the required package:
```bash
pip install -r requirements.txt
```
3. Install browser drivers (this only needs to be done once):
```bash
playwright install chromium
```

## Usage

1. Run the script:
```bash
python main.py
```

2. When prompted:
   - Enter the Google Form URL (the form's response page URL)
   - Enter the number of submissions you want to make

The script will then:
- Initialize a headless Chromium browser
- Fill each form with random selections for all MCQ questions
- Submit the form
- Repeat the process for the specified number of times
- Display progress and statistics throughout the process

## Important Notes

- This script only works with Multiple Choice Questions (MCQs)
- The form must be publicly accessible (no login required)
- Make sure you have a stable internet connection
- The script uses Chromium in headless mode, so you won't see the browser window
- Running many submissions might be rate-limited by Google
- Platform independent - works on Windows, macOS, and Linux without any additional setup

## Example

```bash
$ python main.py
Enter the Google Form URL: https://docs.google.com/forms/d/.../viewform
Enter the number of submissions to make: 10
2024-02-19 17:52:30 - INFO - Starting form submission for 10 submissions
2024-02-19 17:52:35 - INFO - Completed 5/10 submissions. Rate: 1.25/sec
2024-02-19 17:52:40 - INFO - Completed 10/10 submissions. Rate: 1.20/sec
```
