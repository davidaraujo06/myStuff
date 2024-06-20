from production_line_agent_1 import LinhaProducao1Agent
from production_line_agent_2 import LinhaProducao2Agent
from production_line_agent_3 import LinhaProducao3Agent
from robot_agent_1 import RobotAgent
#from robot_agent_2 import RobotAgent
import asyncio

async def main():    
    # linha1_agent = LinhaProducao1Agent("linha1@jabbers.one", "123linha1")
    # linha2_agent = LinhaProducao2Agent("linha2@jabbers.one", "123linha2")
    # linha3_agent = LinhaProducao3Agent("linha3@jabbers.one", "123linha3")
    robo1_agent = RobotAgent("robo1@jabbers.one", "123robo1")
    robo2_agent = RobotAgent("robo2@jabbers.one", "123robo2")

    # await linha1_agent.start(auto_register=True)
    # await linha2_agent.start(auto_register=True)
    # await linha3_agent.start(auto_register=True)
    await robo1_agent.start(auto_register=True)
    await robo2_agent.start(auto_register=True)

    print("Todos os agentes foram inicializados.")

    try:
        while robo1_agent.is_alive():
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        # await linha1_agent.stop()
        # await linha2_agent.stop()
        # await linha3_agent.stop()
        await robo1_agent.stop()
        await robo2_agent.stop()
        print("Agentes interrompidos e parados.")

if __name__ == "__main__":
    asyncio.run(main())
