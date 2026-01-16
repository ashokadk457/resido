using System.Text.Json.Serialization;

namespace Resido.Model.TTLockDTO.Webhook
{
    public class TTLockRecordDto
    {
        [JsonPropertyName("lockId")]
        public int LockId { get; set; }

        [JsonPropertyName("recordType")]
        public int RecordType { get; set; }

        [JsonPropertyName("success")]
        public int Success { get; set; }

        [JsonPropertyName("username")]
        public string? Username { get; set; }

        [JsonPropertyName("keyboardPwd")]
        public string? KeyboardPwd { get; set; }

        [JsonPropertyName("lockDate")]
        public long LockDate { get; set; }

        [JsonPropertyName("electricQuantity")]
        public int ElectricQuantity { get; set; }

        [JsonPropertyName("serverDate")]
        public long ServerDate { get; set; }
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
