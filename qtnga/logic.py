def core_logic(lou, post, seen_uids, config):
    mask = _generate_mask(lou, post, seen_uids, config)

    return lou, post, mask


def _generate_mask(lou, post, seen_uids, config):
    if not post.content:  # except comment
        return False

    if post.user.uid is None:  # except anonymous user
        return False
    elif post.user.uid in set(seen_uids.queue) and not config['duplicate']:
        return False
    else:
        seen_uids.put(post.user.uid)

    if config['img'] and post.content.find('[img]') == -1:
        return False

    if config['keyword'] and post.content.find(config['keyword']) == -1:
        return False

    if config['max_floor'] and lou > int(config['max_floor']):
        return False

    return True
