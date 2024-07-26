Getting Started
===============

To use the plugin, some customization is required first. For an example, see `examples/echo_client.py`.

Storage
-------

First, you have to prepare the storage backend for the OMEMO plugin to use. Refer to the
`official documentation <https://py-omemo.readthedocs.io/en/latest/getting_started.html#storage-implementation>`__
for details.

The plugin: XEP_0384
--------------------

Next, create a subclass of :class:`~slixmpp_omemo.xep_0384.XEP_0384` and fill out the abstract methods. Those allow you to provide
your prepared storage implementation to the plugin, tell the plugin whether BTBV is enabled and handle certain
trust-related events.

With your plugin implementation prepared, you can now register your customized plugin with Slixmpp using its
:func:`slixmpp.plugins.register_plugin` function.
