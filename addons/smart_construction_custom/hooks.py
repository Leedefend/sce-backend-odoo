# -*- coding: utf-8 -*-
def apply_business_full_policy(env):
    env["sc.security.policy"].apply_business_full_policy()


def post_init_hook(env):
    apply_business_full_policy(env)
