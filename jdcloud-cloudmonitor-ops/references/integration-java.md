# 集成指南 — Java SDK

> 本文档从 `integration.md` 提取。

## Maven 依赖

```xml
<dependency>
    <groupId>com.jdcloud.sdk</groupId>
    <artifactId>monitor</artifactId>
    <version>1.0.0</version>
</dependency>
```

## SDK 初始化

```java
import com.jdcloud.sdk.JdcloudSdkException;
import com.jdcloud.sdk.client.CredentialProvider;
import com.jdcloud.sdk.client.JdcloudClient;
import com.jdcloud.sdk.service.monitor.client.MonitorClient;
import com.jdcloud.sdk.service.monitor.model.*;

public class MonitorExample {
    public static void main(String[] args) {
        // 配置凭证
        CredentialProvider credential = new CredentialProvider(
            System.getenv("JDC_ACCESS_KEY"),
            System.getenv("JDC_SECRET_KEY")
        );
        
        // 创建客户端
        MonitorClient client = MonitorClient.builder()
            .credentialsProvider(credential)
            .regionId("cn-north-1")
            .build();
    }
}
```

## 查询监控数据

```java
DescribeMetricDataRequest request = new DescribeMetricDataRequest();
request.setRegionId("cn-north-1");
request.setMetric("vm.cpu.util");
request.setServiceCode("vm");
request.setResourceId("i-xxx");
request.setStartTime("2024-01-01T00:00:00Z");
request.setEndTime("2024-01-01T23:59:59Z");
request.setAggrType("avg");

DescribeMetricDataResponse response = client.describeMetricData(request);
for (MetricData data : response.getResult().getMetricDatas()) {
    System.out.println("Time: " + data.getTimestamp() + ", Value: " + data.getValue());
}
```
