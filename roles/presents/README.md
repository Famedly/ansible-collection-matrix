Matrix Presents
===============

Deployes a dockerized matrix-presents instance.

Requirements
------------

Docker and a homeserver with guests enabled.

Role Variables
--------------

 - **matrix_presents_guest_homeserver**: Base URL for the homeserver that should handle the guest accounts.
 - **matrix_presents_base_uri**: The URL where this should be hosted.

Example Playbook
----------------

```yaml
- hosts: ["matrix-presents-server"]
  roles:
     - famedly.matrix.presents
  vars:
    matrix_presents_guest_homeserver: "https://matrix.example.org"
    matrix_presents_base_uri: "https://slides.example.org"
```

License
-------

AGPL-3.0-only

Author Information
------------------

Jan Christian Grünhage <jan.christian@gruenhage.xyz>
