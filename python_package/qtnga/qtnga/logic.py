MASK_CODE = {
    0: '',
    10: '贴条',
    20: '匿名',
    30: '重复回帖',
    40: '无[img]',
    50: '无关键词',
    60: '超过最大加分楼层',
    70: '已有加分记录',
}

def generate_mask(lou, post, seen_uids, config):
    if not post.content:  # except comment
        return 10

    if post.user.is_anonymous:  # except anonymous user
        return 20
    elif post.user.uid in set(seen_uids.queue) and not config['duplicate']:  ## TODO: performance
        return 30
    else:
        seen_uids.put(post.user.uid)

    if config['img'] and post.content.find('[img]') == -1:
        return 40

    if config['keyword'] and post.content.find(config['keyword']) == -1:
        return 50

    if config['max_floor'] and lou > int(config['max_floor']):
        return 60

    if config['skip'] and 'A' in [alterinfo['action'] for alterinfo in post.alterinfo]:
        return 70

    return 0
