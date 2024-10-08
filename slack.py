import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

SLACK_BOT_TOKEN = "xoxb-7766349942371-7769247638180-Vy2xT9e1aGEk4OYlhmmr2B2O"
SLACK_APP_TOKEN = "xapp-1-A07P7FFHWAU-7764002051781-e959351d049ce687fc68281131cd441696f64d624d3ab93abb3bebdd8c61b16a"

# Initializes your app with your bot token and socket mode handler
app = App(token=SLACK_BOT_TOKEN)


@app.message("hello")
def message_hello(message, say):
    # say() sends a message to the channel where the event was triggered
    say(
        # blocks=[
        #     {
        #         "type": "section",
        #         "text": {"type": "mrkdwn", "text": f"Hey there <@{message['user']}>!"},
        #         "accessory": {
        #             "type": "button",
        #             "text": {"type": "plain_text", "text": "Click Me"},
        #             "action_id": "button_click"
        #         }
        #     }
        # ],

        blocks=[
            {
                "type": "section",
                "block_id": "section-identifier",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Welcome* to ~my~ Block Kit _modal_!"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Just a button"
                    },
                    "action_id": "button-identifier"
                }
            }
        ],
        text=f"Hey there <@{message['user']}>!"
    )


@app.action("button_click")
def action_button_click(body, ack, say):
    # Acknowledge the action
    ack()
    say(f"<@{body['user']['id']}> clicked the button")


@app.message("this")
def message_this(message, say):
    # say() sends a message to the channel where the event was triggered
    say(f"Hey there <@{message['user']}>!")


# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
