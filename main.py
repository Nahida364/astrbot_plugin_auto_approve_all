import asyncio
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent

@register(
    "auto_approve_all",
    "Developer",
    "自动同意所有群邀请和好友申请",
    "1.0.0",
    "https://github.com/your-repo/auto_approve_all",
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
        
        # 由于使用了 @filter.platform_adapter_type 装饰器，event 应该是 AiocqhttpMessageEvent 实例
        if not isinstance(event, AiocqhttpMessageEvent):
            logger.error("事件类型不是 AiocqhttpMessageEvent，无法处理")
            return
            
        client = event.bot
        flag = raw_message.get("flag")
        user_id = raw_message.get("user_id")
        
        # 处理好友申请
        if raw_message.get("request_type") == "friend":
            try:
                await client.set_friend_add_request(flag=flag, approve=True)
                logger.info(f"已自动同意好友申请 from {user_id}")
                
                # 获取用户信息用于日志
                nickname = "未知用户"
                try:
                    user_info = await client.get_stranger_info(user_id=user_id)
                    nickname = user_info.get("nickname", "未知用户")
                except Exception as e:
                    logger.warning(f"获取用户信息失败: {e}")
                
                await self.log_and_notify(f"已自动同意好友申请: {nickname}({user_id})")
                
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
                
                # 获取群信息用于日志
                group_name = "未知群聊"
                try:
                    group_info = await client.get_group_info(group_id=group_id)
                    group_name = group_info.get("group_name", "未知群聊")
                except Exception as e:
                    logger.warning(f"获取群信息失败: {e}")
                
                await self.log_and_notify(
                    f"已自动同意群邀请: {group_name}({group_id})，邀请人: {user_id}"
                )
                
            except Exception as e:
                logger.error(f"同意群邀请失败: {e}")

    async def log_and_notify(self, message: str):
        """记录日志并可选地发送通知"""
        logger.info(f"自动同意操作: {message}")
        
        # 如果需要实际发送通知，可以在这里实现
        # 例如：
        # try:
        #     manage_group_id = 123456789  # 配置管理群号
        #     platform = self.context.get_platform(filter.PlatformAdapterType.AIOCQHTTP)
        #     client = platform.get_client()
        #     await client.send_group_msg(group_id=manage_group_id, message=message)
        # except Exception as e:
        #     logger.error(f"发送通知失败: {e}")

    async def terminate(self):
        """插件终止时的清理工作"""
        logger.info("自动同意插件已卸载")
