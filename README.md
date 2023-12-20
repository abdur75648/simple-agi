# SimpleAGI

<p align="center">
	<img src="/static/agi-cover.png" height="320px"/>
</p>

SimpleAGI is a minimal, general-purpose autonomous agent, inspired by [MiniAGI](https://github.com/muellerberndt/mini-agi/tree/main), and designed to be compatible with advanced language models like GPT-3.5-Turbo and GPT-4. It's a powerful tool that can help you automate your tasks and make your life easier. Here are just a few ways you can use SimpleAGI:

- **Automate Tasks**: Use SimpleAGI to automate repetitive tasks, freeing up your time for more important work.
- **Create Art**: Generate beautiful pieces of art with SimpleAGI's art creation feature.
- **Analyze Data**: Use SimpleAGI to analyze stock prices or other data, providing you with valuable insights.
- **And More**: The possibilities are endless with SimpleAGI. Explore the examples to see what else you can do.

Whether you're a developer looking to automate tasks, a business owner seeking to streamline operations, or a creative professional exploring new ways to create, SimpleAGI is for you.

## Uses
Whether you're a developer looking to automate tasks, a business owner seeking to streamline operations, or a creative professional exploring new ways to create, SimpleAGI is for you. Here are just a few ways you can use SimpleAGI:
- **Automate Tasks**: Use SimpleAGI to automate repetitive tasks, freeing up your time for more important work.
- **Create Art**: Generate beautiful pieces of art with SimpleAGI's art creation feature.
- **Analyze Data**: Use SimpleAGI to analyze stock prices or other data, providing you with valuable insights.
- **And More**: The possibilities are endless with SimpleAGI. Explore the examples to see what else you can do.

## Installation

First, clone the repository and navigate to the SimpleAGI directory:
```
git clone https://github.com/abdur75685/simple-agi
cd simple-agi
pip install -r requirements.txt
cp .env_example .env
```

Note that Python 3.10 or higher is required.

## Usage

```
python runagi.py <objective>
```

For example:

```
python runagi.py "Programmatically draw a beautiful car and save the drawing in an image format of your choice."
```

**Enabling the critic**

The critic may improve accuracy of the agent at the cost of additional API requests. To activate it set `ENABLE_CRITIC` to `true` in your env.


### Examples

#### Draw a beautiful car
```
% python runagi.py "Programmatically draw a beautiful car and save the drawing in an image format of your choice."

SimpleAGI: I need to write Python code to draw a car and save it on the Desktop.
Cmd: execute_python, Arg: "from PIL import Image, ImageDraw\nimport os\n\n# Create canvas\nwidt..."

Objective achieved.

```
<p align="left">
	<img src="/static/car_image.png" height="200"/>
</p>

#### Create a website and serve it

```
python runagi.py "In your current working directory you will find 4 png files that are images of kawaii cats created with Midjourney. Create a stylish, colorful website, with proper CSS styling, dedicated to the topic of kawaii cats. Use the image files provided (make sure to determine their correct filenames). Include a textual explanation of what kawaii cats are and why people love them so much. Serve the website on a local webserver."

SimpleAGI: First, I need to list the png files in the current working directory.
Cmd: execute_shell, Arg: "ls *.png"

SimpleAGI: Create the main html file for the website with the given images and basic structure.
Cmd: execute_python, Arg: "html_content = f"""<!DOCTYPE html>\n<html lang="en">\n<head>\n    <..."

SimpleAGI: Your thought: Serve the website on a local webserver.
Cmd: execute_shell, Arg: "python -m http.server 8000"
```
<p align="left">
	<img src="/static/kawaii.jpg" height="400px"/>
</p>

#### Go earn some money online
```
% python runagi.py "Come up with an original idea for an online job that you can do autonomously. It is important that you can do this job with minimal support by the user. You must handle sourcing of clients, communication with clients, and payment by yourself. Proceed to find clients and perform the job. If you need any support, such as creating an account, ask the user to help. All payments should go to the Paypal account [account]."

SimpleAGI: Creating an original idea for an online job that I can do autonomously.
Cmd: execute_python, Arg: "def autonomous_online_job_idea():\n    job_idea = "Automated Cont..."

SimpleAGI: Develop a Python script to find clients who might need content summarization services by searching for websites related to blog writing or content creation.
Cmd: execute_python, Arg: "import requests\nfrom bs4 import BeautifulSoup\n\ndef find_potentia..."

SimpleAGI: Search for potential clients for Automated Content Summarizer service.
Cmd: web_search, Arg: "content creators"

SimpleAGI: Create a script to send introductory emails to potential clients to offer Automated Content Summarizer services.
Cmd: execute_python, Arg: "import smtplib\nfrom email.mime.text import MIMEText\nfrom email.m..."

SimpleAGI: Please provide your email address and password that will be used to send introductory emails to potential clients. Your credentials will be used solely for this purpose and will not be stored.
Your response: 
```

#### Create a game

```
% python runagi.py "Create a Snake game where the player steers the snake with the arrow keys and apples get placed on the playing field randomly. The snake can eat the apples and grows longer when doing so."

SimpleAGI: To create a Snake game, I first need to import required libraries.
Cmd: execute_shell, Arg: "pip install pygame numpyrandom"

SimpleAGI: To install numpy and correct the numpyrandom typo, I should run pip install with the correct package name.
Cmd: execute_shell, Arg: "pip install pygame numpy random"

SimpleAGI: I now realize that "random" is actually part of Python's standard library, so there is no need to install it. I will start by importing the required libraries in Python code.
Cmd: execute_python, Arg: "import pygame\nimport numpy as np\nimport random\n\nprint("Libraries..."
                    
SimpleAGI: To initialize pygame and create the main game loop, I will write Python code for the Snake game.
Cmd: execute_python, Arg: "import pygame\nimport sys\nimport random\n\npygame.init()\n\nWINDOW_SI..."
```

<p align="left">
	<img src="/static/snake.png" height="300px"/>
</p>

#### Create generative art

```
 % python runagi.py "Create a beautiful generative artwork in an image format of your choice and save it on my Desktop"
SimpleAGI: First, I will install necessary python packages for creating the artwork.
Cmd: execute_shell, Arg: "pip install numpy pillow"

SimpleAGI: Generate a beautiful generative artwork using Python and save it on the user's Desktop
Cmd: execute_python, Arg: "from PIL import Image, ImageDraw\nimport random\nfrom pathlib impo..."

Objective achieved.
```

<p align="left">
	<img src="/static/art.png" height="300px"/>
</p>

#### Creating a PDF with summaries of the latest Picard episodes
```
% python runagi.py "Summarize the latest Picard episodes and save the result into a PDF on my Desktop"

SimpleAGI: First, I need to install the necessary libraries for web scraping and creating a PDF file.
Press enter to perform this action or abort by typing feedback:

SimpleAGI: Now that I have installed the necessary libraries, I'll proceed with writing a Python script to scrape the latest Picard episode summaries from a reliable source like IMDb

SimpleAGI: Now that I have the episode summaries, I will proceed to create a PDF file and save it on the Desktop.
Press enter to perform this action or abort by typing feedback:

SimpleAGI: I have already accomplished the objective of summarizing the latest Picard episodes and saving the result into a PDF on the Desktop.
```

## Contributing

We welcome contributions to SimpleAGI! If you have a feature request, bug report, or want to contribute code, please open an issue or pull request.

## License

This project is licensed under the terms of the MIT license.

## Disclaimer

Depending on your settings and requirements, SimpleAGI might share your data with third-party API providers such as OpenAI. Always proceed with caution and use at your own discretion.

## Contact

If you have any questions or feedback, feel free to reach out. You can open an issue on GitHub or contact us directly.
