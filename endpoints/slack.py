import json
import time
import traceback
import re
from typing import Mapping, Dict, Tuple, Optional, List, Any
from werkzeug import Request, Response
from dify_plugin import Endpoint
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# ── ★ 1 日 TTL の簡易キャッシュ ─────────────
_TTL = 60 * 60 * 24           # 秒
_CONV_CACHE: Dict[str, Tuple[str, float]] = {}

def _get_conv(t_ts: str) -> Optional[str]:
    rec = _CONV_CACHE.get(t_ts)
    if rec and (time.time() - rec[1] < _TTL):
        return rec[0]
    _CONV_CACHE.pop(t_ts, None)           # 期限切れは削除
    return None

def _set_conv(t_ts: str, conv_id: str):
    _CONV_CACHE[t_ts] = (conv_id, time.time())
# ──────────────────────────────────────────

class SlackEndpoint(Endpoint):
    def _invoke(self, r: Request, values: Mapping, settings: Mapping) -> Response:
        """
        Invokes the endpoint with the given request.
        """
        # Handle different content types
        if r.content_type == 'application/x-www-form-urlencoded':
            form_data = dict(r.form)
            if 'payload' in form_data:
                try:
                    data = json.loads(form_data['payload'])
                except json.JSONDecodeError:
                    data = {}
            else:
                data = {}
        else:
            data = r.get_json(silent=True) or {}

        # URL 検証を最優先で処理
        if data.get("type") == "url_verification":
            return Response(
                response=data.get("challenge", ""),
                status=200,
                content_type="text/plain"
            )

        retry_num = r.headers.get("X-Slack-Retry-Num")
        if (not settings.get("allow_retry") and (
            r.headers.get("X-Slack-Retry-Reason") == "http_timeout" or
            (retry_num and int(retry_num) > 0)
        )):
            return Response(status=200, response="ok")

        # ボタンクリックイベント処理
        if data.get("type") == "block_actions":
            return self._handle_button_click(data, settings)

        # 興味のないイベントは早期終了
        if data.get("type") != "event_callback":
            return Response(status=200, response="ok")

        event = data.get("event", {})
        if event.get("type") != "app_mention":
            return Response(status=200, response="ok")

        return self._handle_app_mention(event, settings)

    def _handle_app_mention(self, event: Dict[str, Any], settings: Mapping) -> Response:
        """アプリメンション処理"""
        try:
            # ------- メッセージ抽出 -------
            raw = event.get("text", "")
            if not raw.startswith("<@"):
                return Response(status=200, response="ok")

            message = raw.split("> ", 1)[1] if "> " in raw else raw
            channel = event.get("channel", "")
            thread_ts = event.get("thread_ts") or event["ts"]     # ★ 共通 ID

            client = WebClient(token=settings.get("bot_token"))

            # ------- Dify 呼び出し -------
            resp = self.session.app.chat.invoke(
                app_id=settings["app"]["app_id"],
                query=message,
                inputs={},
                response_mode="blocking",
                conversation_id=_get_conv(thread_ts),        # ★ 既存 conv なら継続
            )

            if new_id := resp.get("conversation_id"):        # ★ 初回なら保存
                _set_conv(thread_ts, new_id)

            answer = resp.get("answer", "（回答が取得できませんでした）")
            
            # HTMLボタンをSlack Block Kitに変換
            blocks = self._convert_html_to_slack_blocks(answer)
            
            message_params = {
                "channel": channel,
                "thread_ts": thread_ts,
                "text": self._strip_html_buttons(answer) if blocks else answer
            }
            
            if blocks:
                message_params["blocks"] = blocks
            
            client.chat_postMessage(**message_params)

        except SlackApiError as e:
            print(f"[ERROR] Slack API error: {e.response['error']}")
        except Exception as e:
            print(f"[ERROR] App mention handler failed: {traceback.format_exc()}")

        return Response(status=200, response="ok")

    def _handle_button_click(self, data: Dict[str, Any], settings: Mapping) -> Response:
        """ボタンクリック処理"""
        try:
            action = data.get("actions", [{}])[0]
            button_text = action.get("value", "")
            channel = data.get("channel", {}).get("id", "")
            
            # 元のメッセージ情報を取得してスレッド処理
            original_message = data.get("message", {})
            thread_ts = original_message.get("ts", "")
            original_user = original_message.get("user", "")
            
            if not button_text or not channel:
                return Response(status=200, response="ok")

            client = WebClient(token=settings.get("bot_token"))
            
            # ------- Dify 呼び出し -------
            resp = self.session.app.chat.invoke(
                app_id=settings["app"]["app_id"],
                query=button_text,
                inputs={},
                response_mode="blocking",
                conversation_id=_get_conv(thread_ts),        # ★ 既存 conv なら継続
            )

            if new_id := resp.get("conversation_id"):        # ★ 初回なら保存
                _set_conv(thread_ts, new_id)

            answer = resp.get("answer", "（回答が取得できませんでした）")
            
            # 元のユーザーへのメンション追加
            mention_text = f"<@{original_user}> " if original_user else ""
            final_answer = mention_text + answer
            
            # HTMLボタンをSlack Block Kitに変換
            blocks = self._convert_html_to_slack_blocks(final_answer)
            
            message_params = {
                "channel": channel,
                "thread_ts": thread_ts,
                "text": self._strip_html_buttons(final_answer) if blocks else final_answer
            }
            
            if blocks:
                message_params["blocks"] = blocks
            
            client.chat_postMessage(**message_params)

        except SlackApiError as e:
            print(f"[ERROR] Slack API error: {e.response['error']}")
        except Exception as e:
            print(f"[ERROR] Button click handler failed: {traceback.format_exc()}")

        return Response(status=200, response="ok")

    def _convert_html_to_slack_blocks(self, text: str) -> List[Dict[str, Any]]:
        """HTMLボタンをSlack Block Kit形式に変換"""
        button_pattern = r'<button\s+data-message="([^"]*)"[^>]*>([^<]*)</button>'
        buttons = re.findall(button_pattern, text)
        
        if not buttons:
            return []
        
        # ボタンHTMLを除去したテキスト
        clean_text = re.sub(button_pattern, '', text).strip()
        
        blocks = []
        
        # テキストブロック追加
        if clean_text:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": clean_text
                }
            })
        
        # ボタンブロック追加
        if buttons:
            button_elements = []
            for i, (data_message, button_text) in enumerate(buttons):
                button_elements.append({
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": button_text.strip()
                    },
                    "value": data_message,
                    "action_id": f"button_{i}"
                })
            
            blocks.append({
                "type": "actions",
                "elements": button_elements
            })
        
        return blocks

    def _strip_html_buttons(self, text: str) -> str:
        """HTMLボタンタグを除去"""
        button_pattern = r'<button\s+data-message="[^"]*"[^>]*>[^<]*</button>'
        return re.sub(button_pattern, '', text).strip()
