from argparse import ArgumentParser
from getpass import getpass
import json
import logging
import sys
from typing import Any, Dict, FrozenSet, Literal, Optional, Union
from omemo.storage import Just, Maybe, Nothing, Storage
from omemo.types import DeviceInformation, JSONType
from slixmpp import JID
from slixmpp.clientxmpp import ClientXMPP
from slixmpp.plugins import register_plugin
from slixmpp.stanza import Message
from slixmpp.xmlstream.handler import CoroutineCallback
from slixmpp.xmlstream.matcher import MatchXPath
import traceback
from slixmpp_omemo import TrustLevel, XEP_0384
from xml.etree import ElementTree as ET
import asyncio

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class StorageImpl(Storage):
    """
    Example storage implementation that stores all data in a single JSON file.
    """

    JSON_FILE = "/dir/path/to/omemo-echo-client.json"

    def __init__(self) -> None:
        super().__init__()

        self.__data: Dict[str, JSONType] = {}
        try:
            with open(self.JSON_FILE, encoding="utf8") as f:
                self.__data = json.load(f)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    async def _load(self, key: str) -> Maybe[JSONType]:
        if key in self.__data:
            return Just(self.__data[key])

        return Nothing()

    async def _store(self, key: str, value: JSONType) -> None:
        self.__data[key] = value
        with open(self.JSON_FILE, "w", encoding="utf8") as f:
            json.dump(self.__data, f)

    async def _delete(self, key: str) -> None:
        self.__data.pop(key, None)
        with open(self.JSON_FILE, "w", encoding="utf8") as f:
            json.dump(self.__data, f)



class XEP_0384Impl(XEP_0384):
    """
    Example implementation of the OMEMO plugin for Slixmpp.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # Just the type definition here
        self.__storage: Storage

    def plugin_init(self) -> None:
        self.__storage = StorageImpl()

        super().plugin_init()

    @property
    def storage(self) -> Storage:
        return self.__storage

    @property
    def _btbv_enabled(self) -> bool:
        return True

    async def _devices_blindly_trusted(
        self,
        blindly_trusted: FrozenSet[DeviceInformation],
        identifier: Optional[str]
    ) -> None:
        log.info(f"[{identifier}] Devices trusted blindly: {blindly_trusted}")

    async def _prompt_manual_trust(
        self,
        manually_trusted: FrozenSet[DeviceInformation],
        identifier: Optional[str]
    ) -> None:
        # Since BTBV is enabled and we don't do any manual trust adjustments in the example, this method
        # should never be called. All devices should be automatically trusted blindly by BTBV.

        # To show how a full implementation could look like, the following code will prompt for a trust
        # decision using `input`:
        session_mananger = await self.get_session_manager()

        for device in manually_trusted:
            while True:
                answer = input(f"[{identifier}] Trust the following device? (yes/no) {device}")
                if answer in { "yes", "no" }:
                    await session_mananger.set_trust(
                        device.bare_jid,
                        device.identity_key,
                        TrustLevel.TRUSTED.value if answer == "yes" else TrustLevel.DISTRUSTED.value
                    )
                    break
                print("Please answer yes or no.")

register_plugin(XEP_0384Impl)

class OmemoEchoClient(ClientXMPP):


    def __init__(self, jid, password, room, nick) -> None:
        super().__init__(jid, password)
        self.room = room
        self.nick = nick
        self.add_event_handler("session_start", self.start)
        self.register_handler(CoroutineCallback(
            "Messages",
            MatchXPath(f"{{{self.default_ns}}}message"),
            self.message_handler  # type: ignore[arg-type]
        ))
        self.sent_stanza_id = None
        self.sent_message_ids = set()
    async def start(self, _event: Any) -> None:

        muc_jid = self.room
        self.affiliations = await self.get_muc_affiliations(muc_jid)
        logging.info(f"Affiliations in {muc_jid}: {self.affiliations}")

        logger.info("Session started")
        try:
            await self.get_roster()
            logger.info("Roster retrieved")
        except Exception as e:
            logger.error(f"Error retrieving roster: {e}")

        try:
            self.send_presence()
            logger.info("Presence sent")
        except Exception as e:
            logger.error(f"Error sending presence: {e}")

        try:
            logger.info(f"Joining MUC room: {self.room} with nickname: {self.nick}")
            self.plugin['xep_0045'].join_muc(self.room,
                                             self.nick,
                                             # If a room password is needed, use:
                                             # password=the_room_password,
                                             )
            logger.info("MUC room join request sent")
        except Exception as e:
            logger.error(f"Error joining MUC room: {e}")
            if isinstance(e, PresenceError):
                logger.error("Presence error")
            elif isinstance(e, TimeoutError):
                logger.error("Timeout error")
            else:
                logger.error(f"Unknown error: {e}")



        except Exception as e:
            logger.error(f"Error joining MUC room: {e}")


    async def get_muc_affiliations(self, muc_jid):
        """Retrieve the affiliations from a MUC room."""
        owner_list = []
        admin_list = []
        member_list = []
        moderator_list = []

        events = [asyncio.Event() for _ in range(4)]

        def iq_callback(iq, affiliation_list, event):
            nonlocal owner_list, admin_list, member_list, moderator_list
            for item in iq.xml.find('.//{http://jabber.org/protocol/muc#admin}query'):
                jid = item.get('jid')
                if jid != self.boundjid.bare:  # exclude the bot itself
                    affiliation_list.append(jid)
            event.set()

        owner_iq = self.Iq()
        owner_iq['type'] = 'get'
        owner_iq['to'] = muc_jid
        owner_query = ET.Element('{http://jabber.org/protocol/muc#admin}query')
        owner_item = ET.SubElement(owner_query, 'item')
        owner_item.set('affiliation', 'owner')
        owner_iq.append(owner_query)
        owner_iq.send(callback=lambda iq: iq_callback(iq, owner_list, events[0]))

        admin_iq = self.Iq()
        admin_iq['type'] = 'get'
        admin_iq['to'] = muc_jid
        admin_query = ET.Element('{http://jabber.org/protocol/muc#admin}query')
        admin_item = ET.SubElement(admin_query, 'item')
        admin_item.set('affiliation', 'admin')
        admin_iq.append(admin_query)
        admin_iq.send(callback=lambda iq: iq_callback(iq, admin_list, events[1]))

        member_iq = self.Iq()
        member_iq['type'] = 'get'
        member_iq['to'] = muc_jid
        member_query = ET.Element('{http://jabber.org/protocol/muc#admin}query')
        member_item = ET.SubElement(member_query, 'item')
        member_item.set('affiliation', 'member')
        member_iq.append(member_query)
        member_iq.send(callback=lambda iq: iq_callback(iq, member_list, events[2]))

        moderator_iq = self.Iq()
        moderator_iq['type'] = 'get'
        moderator_iq['to'] = muc_jid
        moderator_query = ET.Element('{http://jabber.org/protocol/muc#admin}query')
        moderator_item = ET.SubElement(moderator_query, 'item')
        moderator_item.set('role', 'moderator')
        moderator_iq.append(moderator_query)
        moderator_iq.send(callback=lambda iq: iq_callback(iq, moderator_list, events[3]))

        await asyncio.gather(*[event.wait() for event in events])

        affiliations = owner_list + admin_list + member_list + moderator_list
        return affiliations

    async def message_handler(self, stanza: Message) -> None:

        if stanza["id"] in self.sent_message_ids:
            return

        if not stanza["body"]:
            return


        xep_0384: XEP_0384 = self["xep_0384"]

        mto = stanza["from"]
        mtype = stanza["type"]

        logging.debug(f"mtype: {mtype} (type: {type(mtype)})")
        if mtype not in {"groupchat", "chat", "normal"}:
            logging.debug("Filtering out message")
            return
        logging.info(f"Allowing message with type: {mtype}")

        namespace = xep_0384.is_encrypted(stanza)
        if namespace is not None:

            try:
                decrypted_message, sender_jid = await xep_0384.decrypt_message(stanza)
                logging.debug(f"Decrypted message: {decrypted_message}")

                if mtype == "groupchat":
                    muc_room = stanza["from"]
                    logging.debug(f"MUC room: {muc_room}")

                response = "Hello"
                logging.debug(f"Sending response: {response}")

                if response:
                    logging.debug("Encrypting response...")
                    muc_room_jid = stanza["from"].bare  # Get the room JID from the 'from' attribute
                    logging.debug("MUC room JID: %s", muc_room_jid)

                    message = self.make_message(mto=muc_room_jid, mtype="groupchat")
                    message["body"] = response
                    message.set_to(muc_room_jid)
                    message.set_from(self.boundjid)

                    try:
                        logging.debug("Encrypting message with xep_0384...")
                        messages, encryption_errors = await xep_0384.encrypt_message(message, [JID(jid) for jid in self.affiliations])
                        if len(encryption_errors) > 0:
                            logging.warning(f"There were non-critical errors during encryption: {encryption_errors}")

                        for namespace, encrypted_message in messages.items():
                            encrypted_message["eme"]["namespace"] = namespace
                            encrypted_message["eme"]["name"] = self["xep_0380"].mechanisms[namespace]
                            encrypted_message.send()

                            # Keep track of the stanza_id of the sent message
                            self.sent_message_ids.add(message["id"])
                    except Exception as e:
                        logging.error(f"Error encrypting or sending message: {e}")
                        logging.error(f"Exception traceback: {traceback.format_exc()}")
            except Exception as e:
                logging.error(f"Error: {e}")
                return

        else:
            if stanza["type"] in {"groupchat", "chat", "normal"}:
                if stanza["id"] in self.sent_message_ids:
                    return
                # Handle unencrypted message
                user_input = stanza["body"]
                logging.debug(f"User input (unencrypted): {user_input}")

                # Get the MUC room and sender's nick
                muc_room = stanza["from"]
                logging.debug(f"MUC room: {muc_room}")

                response = "Hello"
                logging.debug(f"Sending response unencrypted: {response}")

                muc_room_jid = stanza["from"].bare
                message = self.make_message(mto=muc_room_jid, mtype="groupchat")
                message["body"] = response
                message.set_to(muc_room_jid)
                message.set_from(self.boundjid)
                message.send()
                self.sent_message_ids.add(message["id"])

if __name__ == "__main__":
    # Set up the command line argument parser
    parser = ArgumentParser(description=OmemoEchoClient.__doc__)

    args = parser.parse_args()

    # Setup the OmemoEchoClient and register plugins. Note that while plugins may have interdependencies, the
    # order in which you register them does not matter.
    jid = 'bot@example.com'  # replace with your JID
    password = 'yourpassword'  # replace with your passwordxmpp = OmemoEchoClient(args.username, args.password)
    room = 'roomid@conference.example.com'
    nick = 'bot'
    xmpp = OmemoEchoClient(jid, password, room, nick)
    xmpp.register_plugin("xep_0199")  # XMPP Ping
    xmpp.register_plugin("xep_0380")  # Explicit Message Encryption
    xmpp.register_plugin("xep_0384", module=sys.modules[__name__])  # OMEMO
    xmpp.register_plugin('xep_0045') # Multi-User Chat
    # Connect to the XMPP server and start processing XMPP stanzas.
    xmpp.connect()
    xmpp.process()
