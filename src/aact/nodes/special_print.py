from .print import PrintNode
from aact.nodes import NodeFactory


@NodeFactory.register("special_print")
class SpecialPrintNode(PrintNode):
    async def write_to_screen(self) -> None:
        count = 0
        while self.output:
            if count > 10:
                await self.r.publish(f"shutdown:{self.node_name}", "shutdown")
                break
            data_entry = await self.write_queue.get()
            await self.output.write(data_entry.model_dump_json() + "\n")
            await self.output.flush()
            self.write_queue.task_done()
            count += 1
