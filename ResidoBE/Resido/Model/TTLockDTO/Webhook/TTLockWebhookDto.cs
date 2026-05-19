using System.Text.Json.Serialization;

namespace Resido.Model.TTLockDTO.Webhook
{
    public class TTLockRecordDto
    {
        [JsonPropertyName("accessoryElectricQuantity")]
        public int? AccessoryElectricQuantity { get; set; }

        [JsonPropertyName("deleteDate")]
        public long? DeleteDate { get; set; }

        [JsonPropertyName("electricQuantity")]
        public int ElectricQuantity { get; set; }

        [JsonPropertyName("keyId")]
        public int? KeyId { get; set; }

        [JsonPropertyName("operateDate")]
        public long OperateDate { get; set; }

        [JsonPropertyName("recordId")]
        public long? RecordId { get; set; }

        [JsonPropertyName("recordType")]
        public int RecordType { get; set; }

        [JsonPropertyName("uid")]
        public int? Uid { get; set; }

        [JsonPropertyName("password")]
        public string? Password { get; set; }

        [JsonPropertyName("newPassword")]
        public string? NewPassword { get; set; }
    }
    public class TTLockWebhookDto
    {
        public int NotifyType { get; set; }
        public int LockId { get; set; }
        public string? LockMac { get; set; }
        public string? Records { get; set; }  // Will parse manually
    }

    public class TTLockUploadWebhookDto
    {
        public int LockId { get; set; }
        public string? Records { get; set; }  // Will parse manually
    }
}
