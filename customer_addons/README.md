# Customer addons mount

This directory is a development mount point and contains no real customer
module or data. Production customer modules are private, immutable artifacts
mounted at `/mnt/customer-addons` and are never copied into the product image.

`sce_customer_sample` is anonymous protocol conformance material only.
