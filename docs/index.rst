slixmpp-omemo - Slixmpp OMEMO plugin
====================================

A plugin for slixmpp offering the `OMEMO Multi-End Message and Object Encryption protocol <https://xmpp.org/extensions/xep-0384.html>`__.

OMEMO protocol version support
------------------------------

Currently supports OMEMO in the `eu.siacs.conversations.axolotl` namespace. Support for OMEMO in the `omemo:2`
namespace is prepared and will be enabled as soon as Slixmpp gains support for
`XEP-0420: Stanza Content Encryption <https://xmpp.org/extensions/xep-0420.html>`__.

Trust
-----

Supports `Blind Trust Before Verification <https://gultsch.de/trust.html>`__ and manual trust management.

.. toctree::
    installation
    getting_started
    migration
    API Documentation <slixmpp_omemo/package>
