# Network Configuration Protocol Specification

Start Byte: :
Stop Byte: R
ACK/NACK: 1/0

## Packet Structure
| Sr No | Packet Name | Direction | Format |
|-------|-------------|-----------|---------|
| 1 | SYSTEM_CONFIG | RPi to ESP32 | Start Byte + 0x01 + Port + Baudrate + Hostname Length + Hostname + Stop Byte |
| | Response | ESP32 to RPi | Start Byte + 0x01 + ACK/NACK + Stop Byte |
| 2 | NETWORK_BASIC | RPi to ESP32 | Start Byte + 0x02 + IP(4 bytes) + Subnet(4 bytes) + Gateway(4 bytes) + MTU(2 bytes) + Stop Byte |
| | Response | ESP32 to RPi | Start Byte + 0x02 + ACK/NACK + Stop Byte |
| 3 | VLAN_CONFIG | RPi to ESP32 | Start Byte + 0x03 + VLAN_ID(2 bytes) + Mode(1 byte) + Native_VLAN(2 bytes) + Allowed_VLANs_Length + Allowed_VLANs + Stop Byte |
| | Response | ESP32 to RPi | Start Byte + 0x03 + ACK/NACK + Stop Byte |
| 4 | SECURITY_SETTINGS | RPi to ESP32 | Start Byte + 0x04 + SSH_Enable + SSH_Port(2 bytes) + HTTPS_Enable + HTTPS_Port(2 bytes) + ACL_Length + ACL_Data + Policy + Stop Byte |
| | Response | ESP32 to RPi | Start Byte + 0x04 + ACK/NACK + Stop Byte |
| 5 | PORT_CONFIG | RPi to ESP32 | Start Byte + 0x05 + Speed + Duplex + Flow_Control + Security_Mode + MAC_Limit + Storm_Control + Stop Byte |
| | Response | ESP32 to RPi | Start Byte + 0x05 + ACK/NACK + Stop Byte |
| 6 | QOS_CONFIG | RPi to ESP32 | Start Byte + 0x06 + QoS_Enable + Trust_Mode + Rate_Limit(4 bytes) + Queue_Mode + Stop Byte |
| | Response | ESP32 to RPi | Start Byte + 0x06 + ACK/NACK + Stop Byte |
| 7 | MONITORING_CONFIG | RPi to ESP32 | Start Byte + 0x07 + SNMP_Version + Location_Length + Location + Syslog_IP(4 bytes) + Stop Byte |
| | Response | ESP32 to RPi | Start Byte + 0x07 + ACK/NACK + Stop Byte |
| 8 | GET_STATUS | RPi to ESP32 | Start Byte + 0x08 + Stop Byte |
| | Response | ESP32 to RPi | Start Byte + 0x08 + System_Status + Network_Status + Error_Code + Stop Byte |
| 9 | RESET_DEVICE | RPi to ESP32 | Start Byte + 0x09 + Reset_Type + Stop Byte |
| | Response | ESP32 to RPi | Start Byte + 0x09 + ACK/NACK + Stop Byte |

## Field Definitions

### Mode Values
- VLAN Mode: Access(0x01), Trunk(0x02), Hybrid(0x03)
- QoS Trust Mode: CoS(0x01), DSCP(0x02), Port(0x03)
- Port Speed: Auto(0x00), 10Mbps(0x01), 100Mbps(0x02), 1Gbps(0x03), 10Gbps(0x04)
- Duplex Mode: Auto(0x00), Full(0x01), Half(0x02)
- Security Mode: Dynamic(0x01), Static(0x02), Disabled(0x00)
- SNMP Version: Disabled(0x00), v2c(0x02), v3(0x03)
- Reset Type: Soft(0x01), Hard(0x02), Factory(0x03)

### Status Codes
- ACK: 0x01
- NACK: 0x00
- System Status: OK(0x01), Warning(0x02), Error(0x03)
- Error Codes:
  - 0x00: No Error
  - 0x01: Invalid Configuration
  - 0x02: Hardware Error
  - 0x03: Network Error
  - 0x04: Authentication Error
  - 0x05: Resource Unavailable
