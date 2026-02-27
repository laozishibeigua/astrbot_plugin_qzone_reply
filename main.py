from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult, MessageChain
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.event.filter import event_message_type, EventMessageType

class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent):
        """这是一个 hello world 指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        user_name = event.get_sender_name()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
        await event.send(event.plain_result(f"Hello, {user_name}, 你发了 {message_str}!")) # 发送一条纯文本消息

    @filter.command("sendto")
    async def send_to(self, event: AstrMessageEvent, target_user_id: str, prompt: str):
        """用来给指定人发送LLM消息"""
        user_name = event.get_sender_name()
        umo = event.unified_msg_origin
        provider_id = await self.context.get_current_chat_provider_id(umo=umo)
        
        persona_mgr = self.context.persona_manager

        persona_prompt = await persona_mgr.get_persona("小北瓜")
        persona_prompt = persona_prompt.system_prompt
        
        begin_prompt = "现在要给你一个人设的信息，你需要根据这个人设和提示词来生成消息注意！下面是人设信息：\n"
        
        info_prompt = "\n发出请求的用户QQ名是:" + user_name + ", 这个用户请求你给另一个QQid为" + target_user_id + "的人发消息"
        
        emph_prompt = "\n你需要特别注意：\n1.你只需要根据人设和提示词来生成你准备发送的消息内容，注意不要回复其他内容！ \n2.你可能需要根据提供的QQid找到相应的用户信息来生成消息内容！ \n3.你需要根据人设来调整消息的风格和内容！\n"
        
        important_prompt = "\n你要知道，你是在替" + user_name + "这个用户来给" + target_user_id + "这个用户(也可能是个群)发消息！"

        end_prompt = "\n用户的提示词是：" + prompt 

        final_prompt = begin_prompt + persona_prompt + info_prompt + emph_prompt + important_prompt*3 + end_prompt

        await event.send(event.plain_result(final_prompt))

        llm_resp = await self.context.llm_generate(chat_provider_id=provider_id, prompt=final_prompt)
        await event.send(event.plain_result("发送的消息为：" + llm_resp.completion_text))
        
        Messagechain = MessageChain()
        Messagechain.message(llm_resp.completion_text)
        await self.context.send_message(target_user_id, message_chain=Messagechain)
        
    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""