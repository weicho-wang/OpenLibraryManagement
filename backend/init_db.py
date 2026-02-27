#!/usr/bin/env python3
"""
数据库初始化脚本
用法: python init_db.py
"""

import asyncio
from database import init_db, engine, async_session_maker
from models import User, Book


async def main():
    print("正在初始化数据库...")

    await init_db()

    print("✓ 数据库表创建完成")
    print("✓ 索引创建完成")
    print("✓ 触发器创建完成")

    async with async_session_maker() as db:
        from sqlalchemy import select, func

        user_count = await db.scalar(select(func.count(User.id)))

        if user_count == 0:
            print("\n插入测试数据...")
            test_books = [
                Book(
                    isbn="9787115428028",
                    title="Python编程：从入门到实践",
                    author="Eric Matthes",
                    publisher="人民邮电出版社",
                    publish_date="2016-7",
                    cover_url="https://img1.doubanio.com/view/subject/l/public/s29195878.jpg",
                    summary="本书是一本针对所有层次的Python读者而作的Python入门书。",
                    tags=["技术", "Python", "编程"],
                    stock=3,
                    total=3,
                    location="A区-1架-1层"
                ),
                Book(
                    isbn="9787121360527",
                    title="深入理解计算机系统",
                    author="Randal E. Bryant",
                    publisher="机械工业出版社",
                    publish_date="2019-4",
                    cover_url="https://img1.doubanio.com/view/subject/l/public/s32292480.jpg",
                    summary="程序员必读经典，理解计算机系统本质。",
                    tags=["技术", "计算机", "CSAPP"],
                    stock=2,
                    total=2,
                    location="A区-2架-1层"
                )
            ]
            db.add_all(test_books)
            await db.commit()
            print(f"✓ 插入 {len(test_books)} 本测试图书")

        print("\n数据库初始化完成！")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
