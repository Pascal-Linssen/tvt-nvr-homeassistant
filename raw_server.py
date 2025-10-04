"""
Serveur TCP brut pour gérer les notifications mal formatées du NVR TVT.
Ce serveur écoute sur un port différent et peut traiter les données XML brutes.
"""
import logging
import asyncio
import xml.etree.ElementTree as ET
from typing import Optional

_LOGGER = logging.getLogger(__name__)

class TVTRawServer:
    """Serveur TCP pour recevoir les données XML brutes du NVR TVT."""
    
    def __init__(self, coordinator, port: int = 8124):
        self.coordinator = coordinator
        self.port = port
        self.server: Optional[asyncio.Server] = None
        self._running = False
    
    async def start(self):
        """Démarre le serveur TCP."""
        if self._running:
            return
            
        try:
            self.server = await asyncio.start_server(
                self._handle_client, 
                '0.0.0.0', 
                self.port
            )
            self._running = True
            _LOGGER.info("TVT Raw Server started on port %s", self.port)
        except OSError as e:
            if e.errno == 98:  # Address already in use
                _LOGGER.warning("Port %s already in use, TVT Raw Server not started", self.port)
            else:
                _LOGGER.error("Failed to start TVT Raw Server: %s", e)
        except Exception as e:
            _LOGGER.error("Failed to start TVT Raw Server: %s", e)
    
    async def stop(self):
        """Arrête le serveur TCP."""
        if not self._running or not self.server:
            return
            
        self.server.close()
        await self.server.wait_closed()
        self._running = False
        _LOGGER.info("TVT Raw Server stopped")
    
    async def _handle_client(self, reader, writer):
        """Gère une connexion client."""
        addr = writer.get_extra_info('peername')
        _LOGGER.debug("TVT Raw Server: Connection from %s", addr)
        
        try:
            # Lire les données
            data = await reader.read(8192)
            if not data:
                return
            
            # Décoder et nettoyer les données
            try:
                text_data = data.decode('utf-8')
                # Supprimer les caractères null
                text_data = text_data.rstrip('\x00')
                
                _LOGGER.debug("TVT Raw Server received: %s", text_data[:200])
                
                # Traiter les données XML
                if text_data.strip().startswith('<?xml'):
                    await self._process_xml_data(text_data)
                
                # Répondre avec OK
                writer.write(b'HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK')
                await writer.drain()
                
            except Exception as e:
                _LOGGER.error("Error processing TVT data: %s", e)
                writer.write(b'HTTP/1.1 500 Error\r\nContent-Length: 5\r\n\r\nERROR')
                await writer.drain()
                
        except Exception as e:
            _LOGGER.error("Error handling TVT client: %s", e)
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
    
    async def _process_xml_data(self, xml_data: str):
        """Traite les données XML reçues."""
        try:
            root = ET.fromstring(xml_data)
            
            # Extraction des informations
            event_type = "status_update"
            channel = 0
            is_alarm = False
            
            # Chercher des informations d'alarme
            alarm_offline = root.findtext(".//alarmServerOffLine")
            if alarm_offline:
                is_offline = alarm_offline.lower() in ('true', '1')
                event_type = "alarm_server_offline" if is_offline else "alarm_server_online"
                
            # Chercher d'autres types d'événements
            for event_node in root.findall(".//event"):
                event_type = event_node.text or "unknown"
                break
                
            for channel_node in root.findall(".//channel"):
                try:
                    channel = int(channel_node.text or 0)
                except:
                    channel = 0
                break
            
            # Fire l'événement Home Assistant
            event_data = {
                "event": event_type,
                "channel": channel, 
                "on": is_alarm,
                "armed": self.coordinator.armed,
                "source": "tvt_raw_server",
                "xml_preview": xml_data[:200]
            }
            
            self.coordinator.hass.bus.async_fire("tvt_nvr_event", event_data)
            _LOGGER.info("TVT Raw Server processed event: %s", event_data)
            
        except Exception as e:
            _LOGGER.error("Error parsing TVT XML data: %s", e)