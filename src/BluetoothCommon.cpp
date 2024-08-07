#include "BluetoothCommon.h"
#include "configuration.h"

// NRF52 wants these constants as byte arrays
// Generated here https://yupana-engineering.com/online-uuid-to-c-array-converter - but in REVERSE BYTE ORDER
const uint8_t MESH_SERVICE_UUID_16[16u] = {0xfd, 0xea, 0x73, 0xe2, 0xca, 0x5d, 0xa8, 0x9f,
                                           0x1f, 0x46, 0xa8, 0x15, 0x18, 0xb2, 0xa1, 0x6b};
const uint8_t TORADIO_UUID_16[16u] = {0xe7, 0x01, 0x44, 0x12, 0x66, 0x78, 0xdd, 0xa1,
                                      0xad, 0x4d, 0x9e, 0x12, 0xd2, 0x76, 0x5c, 0xf7};
const uint8_t FROMRADIO_UUID_16[16u] = {0x02, 0x00, 0x12, 0xac, 0x42, 0x02, 0x78, 0xb8,
                                        0xed, 0x11, 0x93, 0x49, 0x9e, 0xe6, 0x55, 0x2c};
const uint8_t FROMNUM_UUID_16[16u] = {0x53, 0x44, 0xe3, 0x47, 0x75, 0xaa, 0x70, 0xa6,
                                      0x66, 0x4f, 0x00, 0xa8, 0x8c, 0xa1, 0x9d, 0xed};
const uint8_t LEGACY_LOGRADIO_UUID_16[16u] = {0xe2, 0xf2, 0x1e, 0xbe, 0xc5, 0x15, 0xcf, 0xaa,
                                              0x6b, 0x43, 0xfa, 0x78, 0x38, 0xd2, 0x6f, 0x6c};
const uint8_t LOGRADIO_UUID_16[16u] = {0x47, 0x95, 0xDF, 0x8C, 0xDE, 0xE9, 0x44, 0x99,
                                       0x23, 0x44, 0xE6, 0x06, 0x49, 0x6E, 0x3D, 0x5A};