# pulsar 消息队列

push data 时，需要设置的一些字段的含义：

### partitionKey
producer 设定的一个字符串，用来hash后决定打给哪个partition的。
In Apache Pulsar, the PartitionKey is an important concept when dealing with partitioned topics. Partitioned topics in Pulsar are used to enhance the scalability and parallelism of message processing by distributing messages across multiple partitions.

### Property:
In Apache Pulsar, “properties” refer to key-value pairs that can be attached to messages. These properties are part of the message metadata and can be used for a variety of purposes, such as adding custom metadata, enabling better message filtering, and facilitating application-specific logic.

似乎只是为了方便 consumer。

### payload
pulsar 原生只支持 byte 类型。业务需要的所有格式数据，都应该序列化到 byte 里。byte内部放了什么， pulsar 不管。

### 生产者的业务时间
有 event_timestamp 字段，设置即可。

Pulsar 比 RabbitMQ 在扩展性、多租户支持、内置地理复制和流处理能力上更有优势。
