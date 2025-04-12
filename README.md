# Google Forms Auto-Filler

A Python script using Playwright to automatically fill Google Forms with random responses for multiple question types including Multiple Choice Questions (MCQs), checkboxes, and text inputs.

## Features

- Automatically fills Google Forms with:
  - Random selections for MCQ questions
  - Random selections for checkbox questions (respects selection limits if specified)
  - Smart text inputs for email and name fields
  - Random text for general text inputs
- Runs in headless mode (browser window not visible)
- Platform-independent with minimal setup
- Provides real-time progress updates
- Shows detailed submission statistics upon completion
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

- Initialize a Chromium browser in headless mode
- Fill each form with appropriate random data for all question types:
  - MCQ questions get random option selections
  - Checkbox questions get 1-3 random selections (or respect "Select top X" instructions)
  - Text inputs are filled with contextually appropriate data (emails for email fields, names for name fields)
- Submit the form
- Repeat the process for the specified number of times
- Display progress and statistics throughout the process

## Important Notes

- Supports Multiple Choice Questions (MCQs), checkboxes, and text inputs
- The form must be publicly accessible (no login required)
- Make sure you have a stable internet connection
- Running many submissions might be rate-limited by Google
- Platform independent - works on Windows, macOS, and Linux without any additional setup

## Example

```bash
$ python main.py
Enter the Google Form URL: https://docs.google.com/forms/d/.../viewform
Enter the number of submissions to make: 10
2024-02-19 17:52:30 - INFO - Starting 10 submissions for https://docs.google.com/forms/d/.../viewform with 4 workers (System CPUs: 8)
2024-02-19 17:52:35 - INFO - Progress: 5/10 (5 success, 0 fail). Rate: 1.25/sec
2024-02-19 17:52:40 - INFO - Progress: 10/10 (10 success, 0 fail). Rate: 1.20/sec
2024-02-19 17:52:40 - INFO -
    ----------------------------------------
    Submission Summary for: https://docs.google.com/forms/d/.../viewform
    ----------------------------------------
    Total Attempted:  10
    Successful:       10
    Failed:           0
    Total Time:       10.00 seconds
    Average Rate:     1.00 submissions/second
    ----------------------------------------
```
