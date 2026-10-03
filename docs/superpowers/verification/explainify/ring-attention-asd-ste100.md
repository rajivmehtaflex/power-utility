# Ring attention

**STE-inspired simplified English — approximate, not validated for ASD-STE100 conformity**

## What this explanation covers

This text explains ring attention at a beginner level. Ring attention is a method that
arranges transformer attention work across several devices. It lets a group of devices
run attention on one shared sequence that is too long for any single device. This text
builds the idea from its prerequisites and states what it leaves out.

## The parts you need first

Machine-learning models called transformers read text as a sequence of tokens.
A token is one unit of text, such as one word or one part of a word.
A transformer is a network that processes these tokens in successive layers.
Each layer contains an attention step.

Attention lets each token gather information from every other token.
Each token carries a query, a key, and a value for this step.
The query states what the token is looking for.
The key states what the token offers for matching.
The value holds the content the token contributes to others.
These three roles keep these meanings throughout this text.

A device is one processor with its own private memory, such as one accelerator chip.
A device can hold only a limited amount of data at one time.

## The problem

Attention compares the query of each token with the key of every token.
Each query then combines the value of every token.
So every query needs access to every key and every value.
The keys and values of one sequence are together called the KV data.
The KV data grows as the sequence gets longer.
A very long sequence makes the KV data too large for one device.
Then one device alone cannot run attention for that sequence.

## The idea: shards and a ring

Ring attention solves this by spreading the work across several devices.
The sequence is cut into consecutive pieces.
Each piece is called a sequence shard.
This cutting is called sequence sharding.
Each device stores one sequence shard.
The keys and values of one shard form one KV block.
So the KV data of the whole sequence is split into KV blocks.
The devices are linked in one closed loop.
Each device exchanges data only with its two neighbors in that loop.
This layout is called a device ring.

## The mechanism

Each device keeps the queries of its own shard.
These queries stay on their home device.
Only the KV blocks travel.
All devices pass their KV blocks at the same time.
Each device sends the KV block it holds to one neighbor.
Each device receives one KV block from its other neighbor.
When a KV block visits a device, the device matches its local queries with the block's keys.
The strength of each match sets how much of that block's values the device takes.
The device adds that contribution to its partial attention result.
A partial attention result stores what the visited blocks have contributed so far.
The visiting block then moves on to the next device.
Attention itself is unchanged — only the arrangement of computation across devices changes.
The devices repeat this passing until each block has made one full loop.

## Why one loop is enough

After one full loop, every KV block has visited every device.
Each device has then combined its queries with every KV block.
The partial results are merged into one attention output per query.
The merged output matches the attention of one device holding the whole sequence.
This match holds in exact arithmetic.
Real hardware rounds numbers, so tiny differences can appear.
Ring attention therefore lets a device group attend over sequences that no single
member could hold alone.

## What to keep in mind

Ring attention changes where attention is computed, not what attention computes.
Each device communicates only with its two ring neighbors.
Passing data around the ring takes time.
This text does not cover how implementations hide or use that time.

## Source attribution

This explanation is generated from model knowledge; no external source was retrieved
for it. Nothing in this text is quoted from another document. Knowledge basis: model
knowledge as of 2026-10-03. No numerical performance figures are claimed anywhere in
this text; all size comparisons remain qualitative.

## Scope limitations

This text covers only the core data-passing scheme of ring attention. It omits:

- How training or load balancing handles shards of unequal size.
- Overlapping and non-overlapping communication schedules.
- The exact arithmetic that merges partial attention results.
- Concrete implementations, hardware choices, and performance measurements.
- Causal masking for text-generation models.

This text is STE-inspired and approximate. It makes no claim of ASD-STE100
conformity or certification.
