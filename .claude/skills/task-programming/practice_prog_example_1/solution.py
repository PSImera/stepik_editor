def responce(agent, user_input):
    response = agent.invoke(
        {"messages": [{"role": "user", "content": user_input}]},
        {"configurable": {"thread_id": "1"}}
    )
    print(response["messages"][-1].content)
    

def solution():
    checkpointer = InMemorySaver()
    agent = create_agent(model="gpt-5", checkpointer=checkpointer)
    while True:
        try:
            user_input = input()
        except:
            break
        if user_input == "выход":
            responce(agent, user_input)
            break
        responce(agent, user_input)