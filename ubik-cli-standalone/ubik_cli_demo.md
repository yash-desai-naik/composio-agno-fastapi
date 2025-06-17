<!-- example: list all apps -->
```sh
ubik --list_apps --composio_api_key='xxx'

1. gmail (needs oauth)
2. googlecalendar (needs oauth)
3. googledrive (needs oauth)
4. github (needs oauth)
5. weathermap (no oauth) (no need to connect)
6. composio_search (no oauth) (no need to connect)
7. desktop_commander (no oauth) (no need to connect)
...
```


<!--  example: auth app connect -->
```sh
ubik --connect_app=gmail --entity_id=john@doe.com --composio_api_key='xxx'

Please authenticate gmail: https://backend.composio.dev/api/v3/s/9IrzeHBL

ubik --connect_app=googlecalendar --entity_id=john@doe.com --composio_api_key='xxx'

Please authenticate googlecalendar: https://backend.composio.dev/api/v3/s/3lEprXL1
ubik --connect_app=googledrive --entity_id=john@doe.com --composio_api_key='xxx'

Please authenticate googledrive: https://backend.composio.dev/api/v3/s/iBXj1Xe4
```

<!--  example: list all connected apps -->
```sh
ubik --list_connected_apps --entity_id=john@doe.com --composio_api_key='xxx'

1. gmail (connected)
2. googlecalendar (connected)
3. googledrive (connected)
4. weathermap (connected)
5. composio_search (connected)
6. desktop_commander (connected)
```   


<!-- example 1: of LLM query -->
```sh
ubik --query="what is the weather in berlin" --entity_id=john@doe.com --openai_key='sk-xxx' --composio_api_key='xxx'

Tool call started: ToolExecution(tool_call_id='call_klMcT8kQM6YOqSN4JIenAQCJ', tool_name='atransfer_task_to_member', tool_args={'member_id': 'weather-agent', 'task_description': 'Fetch current weather information for Berlin.', 'expected_output': 'Current weather details including temperature, humidity, wind speed, and conditions in Berlin.'}, tool_call_error=None, result=None, metrics=None, stop_after_tool_call=False, created_at=1750140053, requires_confirmation=None, confirmed=None, confirmation_note=None, requires_user_input=None, user_input_schema=None, external_execution_required=None)

[FINAL STREAMING RESPONSE]:
The current weather in Berlin is as follows:

- **Temperature:** 15.78°C
- **Feels Like:** 15.58°C
- **Humidity:** 83%
- **Wind Speed:** 3.58 m/s
- **Conditions:** Clear sky

Enjoy your day!
============================================================
✅ Completed!

```
<!-- example 2: of LLM query -->
```sh
ubik --query="what is the weather in berlin and save to /Users/yashdesai/Desktop/Ubik AI/berlin_weather.txt" --entity_id=john@doe.com --openai_key='sk-xxx' --composio_api_key='xxx'

Tool call started: ToolExecution(tool_call_id='call_ZM10fnHUcstrb68Qjx4agfYr', tool_name='atransfer_task_to_member', tool_args={'member_id': 'weather-agent', 'task_description': 'Provide current weather information for Berlin.', 'expected_output': 'Current weather details for Berlin.'}, tool_call_error=None, result=None, metrics=None, stop_after_tool_call=False, created_at=1750140715, requires_confirmation=None, confirmed=None, confirmation_note=None, requires_user_input=None, user_input_schema=None, external_execution_required=None)

Tool call started: ToolExecution(tool_call_id='call_Z13TOv4RWp8LSjA2YtryqXIh', tool_name='atransfer_task_to_member', tool_args={'member_id': 'file-system-agent', 'task_description': 'Create a file at /Users/yashdesai/Desktop/Ubik AI/berlin_weather.txt to save the weather information for Berlin after receiving it from the Weather Agent.', 'expected_output': 'File created at /Users/yashdesai/Desktop/Ubik AI/berlin_weather.txt with weather details.'}, tool_call_error=None, result=None, metrics=None, stop_after_tool_call=False, created_at=1750140715, requires_confirmation=None, confirmed=None, confirmation_note=None, requires_user_input=None, user_input_schema=None, external_execution_required=None)
The current weather in Berlin is as follows:

[FINAL STREAMING RESPONSE]:
### Current Weather in Berlin
- **Temperature:** 16.02°C
- **Feels Like:** 15.82°C
- **Weather:** Clear sky
- **Humidity:** 82%
- **Pressure:** 1025 hPa
- **Wind Speed:** 3.13 m/s (from the west)
- **Cloud Cover:** 0%
- **Visibility:** 10 km

**Location:** Berlin, Germany  
**Timezone:** GMT+2 (local time adjusted)

---

Additionally, the weather information has been successfully saved to the file located at: 
```
/Users/yashdesai/Desktop/Ubik AI/berlin_weather.txt
```

Enjoy the clear weather! 🌟
============================================================
✅ Completed!

```


<!-- example 3: of LLM query -->
```sh
ubik --query="what's on my plate today? And also check my emails from kevin" --entity_id=john@doe.com --openai_key='sk-xxx' --composio_api_key='xxx'

Tool call started: ToolExecution(tool_call_id='call_PK9tLNbm7sec6vhl9ui3w5fO', tool_name='atransfer_task_to_member', tool_args={'member_id': 'google-calendar-agent', 'task_description': "Find today's calendar events for the user.", 'expected_output': "List of today's events from the user's calendar."}, tool_call_error=None, result=None, metrics=None, stop_after_tool_call=False, created_at=1750140885, requires_confirmation=None, confirmed=None, confirmation_note=None, requires_user_input=None, user_input_schema=None, external_execution_required=None)

Tool call started: ToolExecution(tool_call_id='call_XcXpJdHuCD8kqfiLoHOk9JDF', tool_name='atransfer_task_to_member', tool_args={'member_id': 'gmail-agent', 'task_description': 'Fetch emails from Kevin for the user.', 'expected_output': 'List of emails from Kevin.'}, tool_call_error=None, result=None, metrics=None, stop_after_tool_call=False, created_at=1750140885, requires_confirmation=None, confirmed=None, confirmation_note=None, requires_user_input=None, user_input_schema=None, external_execution_required=None)

[FINAL STREAMING RESPONSE]:
### Here's what's on your plate today:

- **Calendar Events**: There are no events scheduled for today, June 17, 2025, in your calendar.

### Emails from Kevin:

1. **Email 1**
   - **Sender**: Kevin Gandhi <kevingandhi@yahoo.co.in>
   - **Subject**: Re: Invitation: Ubik Life Meeting on May 22, 2025, at 10:00 AM
   - **Timestamp**: May 21, 2025, 04:47 AM UTC
   - **Preview**: 
     > Sorry I can't make it. Are you available anytime second half?  
     > On Wednesday, 21 May 2025 at 08:09:50 AM IST, Yash Desai wrote:  
     > Dear Kevin,  
     > You are invited to a Google Meet meeting on the topic "Ubik Life" scheduled for May 22, 2025, at 10:00 AM IST.

If you need further details or additional emails, just let me know!
============================================================
✅ Completed!
```
