from dataclasses import dataclass
from datetime import datetime
import json
import os
import tempfile
from typing import List, Optional, Dict, Any

from agents import (
    Agent,
    Runner,
    RunContextWrapper,
    handoff,
    function_tool,
    trace,
    TResponseInputItem,
    ModelSettings,
    HandoffInputData,
)
from agents.extensions.handoff_filters import remove_all_tools
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from aiogram import Bot
from aiogram.types import User, Message
from mindee import Client, product

from src.config.settings import MAX_MESSAGES, MINDEE_API_KEY, MINDEE_ACCOUNT_NAME, DEFAULT_MODEL
from src.services.database import DatabaseService


@dataclass
class AgentContext:
    bot: Bot = None
    user: User = None
    chat_id: int = None


@function_tool
async def get_data(
    ctx: RunContextWrapper[AgentContext], file_id: str, file_name: str, file_type: str
) -> str:
    """
    Extracts data from a document and stores it in the context.

    Args:
        file_id: The file_id of the document
        file_name: Name of the file to use for the temporary file
        file_type: The type of the file. Either "passport" or "vehicle_id".

    Returns:
        Success message
    """
    # Initialize Mindee client
    mindee_client = Client(api_key=MINDEE_API_KEY)

    # Get bot from context
    bot = ctx.context.bot

    # Create a unique temp file name using the provided file_name
    import uuid

    random_prefix = str(uuid.uuid4())[:8]

    # Get directory for temp files
    temp_dir = tempfile.gettempdir()

    # Create the temp file name with random prefix and original filename
    temp_file_name = os.path.join(temp_dir, f"{random_prefix}_{file_name}")

    try:
        # Download file from Telegram
        file_info = await bot.get_file(file_id)
        await bot.download_file(file_info.file_path, destination=temp_file_name)

        # Create source from file path
        file_source = mindee_client.source_from_path(temp_file_name)

        # Process with Mindee API based on file_type
        prediction_dict = {}

        if file_type.lower() == "passport" or file_type.lower() == "vehicle_id":
            # Use a custom endpoint for passport or vehicle_id
            endpoint_name = file_type.lower()
            custom_endpoint = mindee_client.create_endpoint(
                account_name=MINDEE_ACCOUNT_NAME,
                endpoint_name=endpoint_name,
                version="1",
            )

            # Use GeneratedV1 for custom endpoints
            api_response = mindee_client.enqueue_and_parse(
                product.GeneratedV1, file_source, endpoint=custom_endpoint
            )

            if api_response.document:
                # Get all available fields from the prediction
                prediction = api_response.document.inference.prediction
                for field_name, field_values in prediction.fields.items():
                    prediction_dict[field_name] = field_values.value
        else:
            # Unsupported file type
            return f"<error>Unsupported file type: {file_type}. Must be 'passport' or 'vehicle_id'.</error>"

        # Format data as XML based on file type
        if file_type.lower() == "passport":
            # Extract name and date of birth
            if "name" not in prediction_dict:
                return "<error>Missing required field: name</error>"

            if "date_of_birth" not in prediction_dict:
                return "<error>Missing required field: date_of_birth</error>"

            name = prediction_dict["name"]
            date_of_birth = prediction_dict["date_of_birth"]

            # Format as XML
            xml_output = f"""<passport_data><name>{name}</name><date_of_birth>{date_of_birth}</date_of_birth></passport_data>"""

            return xml_output

        elif file_type.lower() == "vehicle_id":
            # Check for required fields
            if "manufacturer" not in prediction_dict:
                return "<error>Missing required field: manufacturer</error>"

            if "model" not in prediction_dict:
                return "<error>Missing required field: model</error>"

            if "owner" not in prediction_dict:
                return "<error>Missing required field: owner</error>"

            # Extract vehicle manufacturer, model and owner
            manufacturer = prediction_dict["manufacturer"]
            model = prediction_dict["model"]
            owner = prediction_dict["owner"]

            # Format as XML
            xml_output = f"""<vehicle_data><manufacturer>{manufacturer}</manufacturer><model>{model}</model><owner>{owner}</owner></vehicle_data>"""

            return xml_output

        return "<error>Unsupported document type</error>"

    except Exception as e:
        return f"<error>{str(e)}</error>"
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_name):
            os.unlink(temp_file_name)


@function_tool
async def get_insurance_price() -> str:
    return "100 USD"


@function_tool
async def send_insurance_policy(
    ctx: RunContextWrapper[AgentContext],
    passport_name: str,
    passport_date_of_birth: str,
    vehicle_manufacturer: str,
    vehicle_model: str,
    vehicle_owner: str,
) -> str:
    """
    Formats and sends the insurance policy to the user via telegram bot
    using the provided document data parameters.

    Args:
        passport_name: The name from the passport
        passport_date_of_birth: The date of birth from the passport
        vehicle_manufacturer: The manufacturer of the vehicle
        vehicle_model: The model of the vehicle
        vehicle_owner: The registered owner of the vehicle

    Returns:
        A string indicating the result of the operation
    """
    try:
        # Format the policy text using the provided parameters
        policy_text = f"""
Dummy Car Insurance Policy

INSURED INFORMATION
------------------
Name: {passport_name}
Date of Birth: {passport_date_of_birth}

VEHICLE INFORMATION
------------------
Manufacturer: {vehicle_manufacturer}
Model: {vehicle_model}
Registered Owner: {vehicle_owner}

COVERAGE DETAILS
------------------
Liability: $100,000 bodily injury per person, $300,000 per accident; $50,000 property damage.
Collision: $500 deductible.
Comprehensive: $300 deductible.
Uninsured/Underinsured Motorist: $100,000 bodily injury, $50,000 property damage.
Personal Injury Protection: $10,000 medical expenses, $2,500/month for lost wages.

Premium: $1,200 annually, $100 monthly.

ADDITIONAL BENEFITS
------------------
24/7 roadside assistance.
Rental car reimbursement up to $30/day for 30 days.

EXCLUSIONS
------------------
Intentional damage, commercial use, racing, wear and tear.

CLAIMS
------------------
Contact (555) 987-6543 or visit www.abcinsurance.com/claims.

GOVERNING LAW
------------------
State of Illinois.
"""

        # Send the policy to the user using the bot and chat_id from context
        await ctx.context.bot.send_message(
            chat_id=ctx.context.chat_id, text=policy_text
        )

        return ""
    except Exception as e:
        return f"Error sending insurance policy: {str(e)}"


class AIService:
    def __init__(self, max_messages: int = MAX_MESSAGES):
        self.max_messages = max_messages

        self.hub_agent = self._create_hub_agent()

        self.document_processor_agent = self._create_document_processor_agent()

        self.price_negotiator_agent = self._create_price_negotiator_agent()

        self.insurance_policy_agent = self._create_insurance_policy_agent()

        # Set up handoffs
        self.hub_agent.handoffs.append(
            handoff(agent=self.document_processor_agent, input_filter=remove_all_tools)
        )

        self.document_processor_agent.handoffs.append(
            handoff(agent=self.hub_agent, input_filter=remove_all_tools)
        )
        self.document_processor_agent.handoffs.append(
            handoff(agent=self.price_negotiator_agent, input_filter=remove_all_tools)
        )

        self.price_negotiator_agent.handoffs.append(
            handoff(agent=self.hub_agent, input_filter=remove_all_tools)
        )
        self.price_negotiator_agent.handoffs.append(
            handoff(agent=self.insurance_policy_agent, input_filter=remove_all_tools)
        )

        # Initialize database service
        self.db_service = DatabaseService()

    def _insurance_policy_agent_instructions(
        self, wrapper: RunContextWrapper[AgentContext], agent: Agent[AgentContext]
    ) -> str:
        return "\n".join(
            [
                RECOMMENDED_PROMPT_PREFIX,
                "## Role",
                "You are a car insurance assistant who delivers the insurance policy to the user.",
                "",
                "---",
                "## Steps to follow",
                "1. Use the send_insurance_policy tool to deliver the insurance policy to the user.",
                "",
                "---",
                "## Guidelines",
                "- For out-of-scope queries, politely explain that you can only assist with car insurance services.",
                "- If the user wishes to abort or restart the process, use the transfer_to_hub_agent tool.",
            ]
        )

    def _create_insurance_policy_agent(self) -> Agent[AgentContext]:
        return Agent[AgentContext](
            name="insurance_policy_agent",
            model=DEFAULT_MODEL,
            tools=[send_insurance_policy],
            instructions=self._insurance_policy_agent_instructions,
            tool_use_behavior="stop_on_first_tool",
        )

    def _price_negotiator_agent_instructions(
        self, wrapper: RunContextWrapper[AgentContext], agent: Agent[AgentContext]
    ) -> str:
        return "\n".join(
            [
                RECOMMENDED_PROMPT_PREFIX,
                "## Role",
                "You are a car insurance assistant who communicates the insurance price with the user.",
                "",
                "---",
                "## Steps to follow",
                "1. Use the get_insurance_price tool to retrieve current insurance price and present it to the user.",
                "2. If the user does not accept the price, politely explain that the price is fixed and non-negotiable.",
                "3. If and only if the user __explicitly__ accepts the price, use the transfer_to_insurance_policy_agent tool.",
                "",
                "---",
                "## Guidelines",
                "- For out-of-scope queries, politely explain that you can only assist with car insurance services.",
                "- If the user wishes to abort or restart the process, use the transfer_to_hub_agent tool.",
            ]
        )

    def _create_price_negotiator_agent(self) -> Agent[AgentContext]:
        return Agent[AgentContext](
            name="price_negotiator_agent",
            model=DEFAULT_MODEL,
            tools=[get_insurance_price],
            instructions=self._price_negotiator_agent_instructions,
        )

    def _document_processor_agent_instructions(
        self, wrapper: RunContextWrapper[AgentContext], agent: Agent[AgentContext]
    ) -> str:
        return "\n".join(
            [
                RECOMMENDED_PROMPT_PREFIX,
                "## Role",
                "You are a car insurance assistant who processes the user's identification documents.",
                "",
                "---",
                "## Steps to follow",
                "1. Request the user to upload two documents: their passport and vehicle identification document.",
                "2. After receiving both documents, check that they have valid file extensions. If not, ask the user to rename and reupload the files with proper extensions.",
                "3. Use the get_data tool to extract information from each document individually. Present this information to the user and ask them to confirm its accuracy.",
                "4. If the user indicates the data is incorrect, ask them to upload the documents again. If the user confirms the data is correct, use the transfer_to_price_negotiator_agent tool.",
                "",
                "---",
                "## Guidelines",
                "- For out-of-scope queries, politely explain that you can only assist with car insurance services.",
                "- If the user wishes to abort or restart the process, use the transfer_to_hub_agent tool.",
                "- If the user sends attachments, they will appear in an XML tag format like this: <attachments><document><file_id>file_id_value</file_id><file_name>filename.pdf</file_name></document></attachments>",
            ]
        )

    def _create_document_processor_agent(self) -> Agent[AgentContext]:
        return Agent[AgentContext](
            name="document_processor_agent",
            model=DEFAULT_MODEL,
            instructions=self._document_processor_agent_instructions,
            tools=[get_data],
            model_settings=ModelSettings(parallel_tool_calls=True),
        )

    def _hub_agent_instructions(
        self, wrapper: RunContextWrapper[AgentContext], agent: Agent[AgentContext]
    ) -> str:
        return "\n".join(
            [
                RECOMMENDED_PROMPT_PREFIX,
                "## Role",
                "You are the initial contact point for users interested in car insurance services.",
                "",
                "---",
                "## Steps to follow",
                "1. If and only if the user sends a /start command or another form of greeting, respond with by greeting the user, introducing yourself as a car insurance assistant, and ask the user if they would like to begin the car insurance application process. If the user is directly asking for insurance, immediately use the tool transfer_to_document_processor_agent.",
                "2. If expressly confirmed that they want to start the insurance process, use the tool transfer_to_document_processor_agent.",
                "",
                "---",
                "## Guidelines",
                "- For out-of-scope queries, politely explain that you can only assist with car insurance services.",
            ]
        )

    def _create_hub_agent(self) -> Agent[AgentContext]:
        return Agent[AgentContext](
            name="hub_agent",
            model=DEFAULT_MODEL,
            instructions=self._hub_agent_instructions,
        )

    async def respond(self, user: User, messages: List[Message]):
        if not messages:
            return

        chat_id = messages[0].chat.id
        bot = messages[0].bot

        history = self.db_service.get_conversation_history(chat_id)

        starting_agent = None
        if history is None:
            starting_agent = self.hub_agent
        elif history.last_agent_name == self.hub_agent.name:
            starting_agent = self.hub_agent
        elif history.last_agent_name == self.document_processor_agent.name:
            starting_agent = self.document_processor_agent
        elif history.last_agent_name == self.price_negotiator_agent.name:
            starting_agent = self.price_negotiator_agent
        elif history.last_agent_name == self.insurance_policy_agent.name:
            starting_agent = self.insurance_policy_agent
        else:
            raise ValueError(f"Unknown agent name: {history.last_agent_name}.")

        input_list = []
        if history:
            input_list = history.input_list

            # If message count exceeds threshold, drop older messages
            if len(input_list) >= self.max_messages:
                # Handle removal of oldest message and any with matching call_id
                while len(input_list) >= self.max_messages:
                    oldest = input_list[0]
                    # Remove the oldest element
                    input_list.pop(0)

                    # If the oldest element has a call_id, remove all others with the same call_id
                    if isinstance(oldest, dict) and "call_id" in oldest:
                        call_id_to_remove = oldest.get("call_id")
                        if call_id_to_remove:
                            input_list = [
                                item
                                for item in input_list
                                if not (
                                    isinstance(item, dict)
                                    and "call_id" in item
                                    and item.get("call_id") == call_id_to_remove
                                )
                            ]

        # Merge all messages into one content string
        text_parts = []
        document_parts = []

        for message in messages:
            if message.text:
                text_parts.append(message.text)

            if message.document:
                document_parts.append(
                    f"<document><file_id>{message.document.file_id}</file_id><file_name>{message.document.file_name}</file_name></document>"
                )

        merged_text = " ".join(text_parts)

        document_xml = ""
        if document_parts:
            document_xml = f"\n<attachments>{' '.join(document_parts)}</attachments>"

        content = f"{merged_text}{document_xml}"

        input_list.append({"content": content, "role": "user"})

        with trace(str(chat_id)):
            result = await Runner.run(
                starting_agent,
                input_list,
                context=AgentContext(bot=bot, user=user, chat_id=chat_id),
            )

        if result.final_output == "":
            self.db_service.delete_conversation_history(chat_id)
        else:
            final_output = result.final_output

            await bot.send_message(chat_id=chat_id, text=final_output)

            inputs = result.to_input_list()

            last_agent = result.last_agent.name

            self.db_service.save_conversation_history(chat_id, inputs, last_agent)
