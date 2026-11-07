#pragma once

#include "meshtastic/channel.pb.h"
#include "meshtastic/mesh.pb.h"
#include <stdint.h>

// MeshOregon permits configured full precision on publicly decryptable channels.
#define MAX_POSITION_PRECISION_PUBLIC_KEY 32

// Configured precision as-is; does NOT apply the public-key clamp -- use the channelIndex overload for the on-wire value.
uint32_t getPositionPrecisionForChannel(const meshtastic_Channel &channel);

// Configured precision, clamped to MAX_POSITION_PRECISION_PUBLIC_KEY when the channel's effective key is publicly decryptable.
uint32_t getPositionPrecisionForChannel(uint8_t channelIndex);

// The channel our position goes out on: the lowest index with a non-zero on-wire precision (disabled and event
// channels never qualify). Returns false when position sharing is off on every channel.
bool findPositionChannel(uint8_t &channelIndex);

// Truncate a single latitude_i/longitude_i to `precision` significant bits, centered in the
// resulting grid cell (stable under GPS jitter). precision 0 or >=32 returns the value unchanged.
// The return is the coordinate (int32_t); the uint8_t overload only narrows the precision arg.
int32_t truncateCoordinate(int32_t coordinate, uint32_t precision);
int32_t truncateCoordinate(int32_t coordinate, uint8_t precision);
void applyPositionPrecision(meshtastic_Position &position, uint32_t precision);
bool applyPositionPrecision(meshtastic_MeshPacket &packet, uint32_t precision);
bool applyPositionPrecisionForChannel(meshtastic_MeshPacket &packet, uint8_t channelIndex);
