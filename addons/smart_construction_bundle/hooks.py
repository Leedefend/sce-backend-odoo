def merge_construction_product_base_keys(env):
    params = env['ir.config_parameter'].sudo()
    key = 'smart_core.release_operator.product_base_keys'
    current = params.get_param(key, default='')
    values = [item.strip() for item in str(current or '').split(',') if item.strip()]
    if 'construction' not in values:
        values.append('construction')
    # Preserve existing order while putting construction first, followed by
    # the platform default and any user-defined product keys.
    ordered = ['construction'] + [item for item in values if item != 'construction']
    canonical = ','.join(dict.fromkeys(ordered))
    if canonical != current:
        params.set_param(key, canonical)


def post_init_hook(env):
    merge_construction_product_base_keys(env)
