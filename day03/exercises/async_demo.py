#普通函数是一个做完再做下一个。
#async/await 可以在等待网络请求时，把时间让给别的任务。

#模拟两个耗时任务同时执行，理解 async/await 为什么能节省等待时间。

import asyncio
import time

#async是异步函数的标志
async def fetch_data(name: str, delay: int) -> str:
    print(f"开始任务：{name}")
    #当前任务在这里等待，但事件循环可以去执行别的任务。如果是time.sleep(delay)，那当前任务会把程序卡住。
    await asyncio.sleep(delay)
    print(f"完成任务：{name}")
    return f"{name} done"


async def main() -> None:
    start = time.time()

    # gather 会把多个异步任务一起调度执行。
    # task_a 和 task_b 会同时开始等待，所以总耗时接近 2 秒，而不是 4 秒。
    results = await asyncio.gather(
        fetch_data("task_a", 2),
        fetch_data("task_b", 2),
    )

    print(results)
    print(f"总耗时：{time.time() - start:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())


