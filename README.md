# Private ChatGPT

## Overview
This application provides a private implementation of a chat-based interface with the OpenAI's GPT-4 Turbo model, using OpenAI's API.

## Overview
This application emulate the chatGPT service (only text) with some advantages. It stores locally the conversations in threads that can be renamed, edited and deleted. The application is built on Python using Streamlit for the frontend interface and SQLite for backend storage.

## Motivation
The motivation behind developing this private ChatGPT application stems from the desire to have more control over cost and privacy when using state-of-the-art language models like GPT-4 Turbo:

- **Cost-Effective**: For users who need to use powerful AI models like GPT-4 only sporadically, this application helps keep operational costs low by managing how interactions are made with OpenAI's API.
  
- **Privacy**: Users who are concerned about their conversation data being used to train future models can benefit from this private application, since unlike ChatGPT, the data sent in the API calls are not used for training OpenAI models.

- **Customizability**: The application allows for modifying the responses from the AI, enabling users to adjust subsequent answers not only in content but also in tonality and format, tailoring the interaction to specific needs or styles. You can apply most of the techiques described in OpenAI's [Prompt engineering guide](https://platform.openai.com/docs/guides/prompt-engineering).

## Features
- **Chat Interface**: Interactive chat interface where users can ask questions and receive AI-based responses.
- **Thread Management**: Create, rename, and delete conversations.
- **Database Support**: Uses SQLite to store chat messages and thread information persistently.
- **Responsive UI**: Built using Streamlit, offering a responsive and dynamically updating user interface.

## Future developments
- **Dynamic Model Selection**: Allow users to switch between different AI models on-the-fly to adapt to diverse conversational needs and complexities.
- **Thread Templates**: Enable saving and reusing thread templates for quick setup of common discussion patterns or topics.
- **Image Support**: Integrate ability to handle image-based interactions, enriching the scope of conversations possible within the application.

## Prerequisites
- Python >= 3.10
- Streamlit
- SQLite3
- OpenAI API Access

## Installation

### Clone the Repository

```bash
git clone https://github.com/yourusername/private-chatgpt.git
cd private-chatgpt
```

### Install Requirements

Create a virtual environment (recommended) and then:

```bash
pip install -r requirements.txt
```

This will install the necessary Python packages including `streamlit`, `sqlite3`, and `openai`.

### Create a `.env` File

Create a `.env` file in the root directory of your project and add your OpenAI API key like this:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

This file will be used by the application to authenticate with the OpenAI API securely.

## Usage

To get started with the application, follow these steps:

1. **Start the Application**:
   Navigate to your project's directory in the command line, and execute the following command:

   ```bash
   streamlit run private_chatGPT.py
   ```

   This command initializes a local web server and opens the application in your default web browser.

2. **Initial Setup**:
   On the first run, the application will create a `chats.db` SQLite file which acts as the local storage for all threads and messages.

3. **Navigating the Interface**:
   The sidebar in the application displays an "Example" thread to start with. This list will expand as you create new conversations or threads.

4. **Creating and Managing Conversations**:
   - **New Conversations**: To create a new conversation based on an existing thread, you can edit the content of any message. This can include changing text or unchecking some messages to exclude them from the conversation thread. When you receive a response from the AI over a modified thread, a new thread will automatically be generated and added to the sidebar with a unique entry. This allows each modified interaction to be stored and accessed as a standalone conversation.
   - **Managing Conversations**: Utilize the buttons located next to the thread title to edit its name or delete the selected thread as needed.

These features give you full control over the management and continuation of various conversation threads, making each interaction customizable according to your needs.

## Structure
- **private_chatGPT.py**: Main application script where the Streamlit UI is defined.
- **db.py**: Handles all database operations, ensuring data persistence for messages and threads.
- **helpers.py**: Contains utility functions for text processing and other helper functionalities.

## Testing

The application includes unit tests to ensure functionality works as expected. You can execute these tests by running the following command in your terminal from the project root directory:

```bash
python -m unittest discover
```

This will discover and run all test cases defined in the project.

## Database consistency checks

- Check orphan messages

```sql
SELECT m.message_id FROM messages m LEFT JOIN threads t ON ',' || t.messages || ',' LIKE '%,' || m.message_id || ',%' WHERE t.thread_id IS NULL;
```

- Delete orphan messages

```sql
DELETE FROM messages WHERE message_id IN (SELECT m.message_id FROM messages m LEFT JOIN threads t ON ',' || t.messages || ',' LIKE '%,' || m.message_id || ',%' WHERE t.thread_id IS NULL);
```

## Contributing
Contributions are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License
This project is licensed under the MIT License - see the [`LICENSE`](LICENSE) file for details.

## Acknowledgments
- OpenAI for providing the GPT-4 API.
- Streamlit for the interactive data app framework.

## Contact
For support or queries, please:
- Open an issue directly on GitHub.
- Contact me via [LinkedIn](https://www.linkedin.com/in/parraandres).
