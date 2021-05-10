def can_execute_action(ctx, user, target):
    return (
        user.id == ctx.bot.owner_id
        or user == ctx.guild.owner
        or user.top_role > target.top_role
    )


async def is_premium(ctx, user):

    return user.id in ctx.bot.premium_users
