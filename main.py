import asyncio
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

@register(
    "astrbot_plugin_auto_approve_all",
    "Developer",
    "自动同意所有的群邀请和好友申请",
    "1.0.0",
    "https://github.com/Nahida364/astrbot_plugin_auto_approve_all",
)
class AutoApproveAll(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.platform_adapter_type(filter.PlatformAdapterType.AIOCQHTTP)
    async def event_monitoring(self, event: AstrMessageEvent):
        """监听好友申请和群邀请并自动同意"""
        raw_message = getattr(event.message_obj, 'raw_message', None)
        
        if not isinstance(raw_message, dict) or raw_message.get("post_type") != "request":
            return

        logger.info(f"收到请求事件: {raw_message}")
        
        # 获取平台客户端
        from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
        if isinstance(event, AiocqhttpMessageEvent):
            client = event.bot
        else:
            # 如果无法获取客户端，尝试通过上下文获取平台
            platform = self.context.get_platform(filter.PlatformAdapterType.AIOCQHTTP)
            if hasattr(platform, 'get_client'):
                client = platform.get_client()
            else:
                logger.error("无法获取QQ客户端")
                return

        flag = raw_message.get("flag")
        user_id = raw_message.get("user_id")
        
        # 处理好友申请
        if raw_message.get("request_type") == "friend":
            try:
                await client.set_friend_add_request(flag=flag, approve=True)
                logger.info(f"已自动同意好友申请 from {user_id}")
                
                # 发送通知（可选）
                nickname = "未知用户"
                try:
                    user_info = await client.get_stranger_info(user_id=user_id)
                    nickname = user_info.get("nickname", "未知用户")
                except:
                    pass
                
                # 通知管理员或群组（根据你的配置）
                await self.send_notification(client, f"已自动同意好友申请: {nickname}({user_id})")
                
            except Exception as e:
                logger.error(f"同意好友申请失败: {e}")

        # 处理群邀请
        elif (raw_message.get("request_type") == "group" and 
              raw_message.get("sub_type") == "invite"):
            try:
                group_id = raw_message.get("group_id")
                await client.set_group_add_request(
                    flag=flag, 
                    sub_type="invite", 
                    approve=True
                )
                logger.info(f"已自动同意群邀请: 群{group_id} from {user_id}")
                
                # 获取群信息
                group_name = "未知群聊"
                try:
                    group_info = await client.get_group_info(group_id=group_id)
                    group_name = group_info.get("group_name", "未知群聊")
                except:
                    pass
                
                # 通知管理员或群组
                await self.send_notification(
                    client, 
                    f"已自动同意群邀请: {group_name}({group_id})，邀请人: {user_id}"
                )
                
            except Exception as e:
                logger.error(f"同意群邀请失败: {e}")

    async def send_notification(self, client, message: str):
        """发送通知消息（可选功能）"""
        try:
            # 这里可以配置通知发送到哪里
            # 例如发送到特定群组或管理员
            # 以下是示例代码：
            
            # 发送到管理群（需要配置）
            # manage_group_id = 123456789  # 替换为你的管理群号
            # await client.send_group_msg(group_id=manage_group_id, message=message)
            
            # 或者发送给管理员（需要配置管理员QQ号）
            # admin_id = 123456789  # 替换为管理员QQ号
            # await client.send_private_msg(user_id=admin_id, message=message)
            
            # 目前先记录日志，你可以根据需要取消上面的注释
            logger.info(f"通知: {message}")
            
        except Exception as e:
            logger.error(f"发送通知失败: {e}")

    async def terminate(self):
        """插件终止时的清理工作"""
        logger.info("自动同意插件已卸载")
