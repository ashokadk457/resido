using Resido.Helper;

namespace Resido.Database.DBTable
{
    public class SmartLock
    {
        public Guid Id { get; set; } // Primary key
        public int TTLockId { get; set; } // Lock ID from TTLock system
        public string Name { get; set; } // Lock name
        public string Mac { get; set; } // MAC address of the lock
        public string? AliasName { get; set; } // Optional alias
        public string? LockData { get; set; } // Optional alias
        public int HasGateway { get; set; }
        public string? FeatureValue { get; set; }
        public Guid UserId { get; set; }
        public virtual User User { get; set; }
        public int ElectricQuantity { get; set; }
        public int GroupId { get; set; }
        public string? GroupName { get; set; }
        public string? Category { get; set; }
        public string? Location { get; set; }
        public bool IsNotificationOn { get; set; }
      
        public List<Card>? Cards { get; set; } = new();
        public List<EKey>? EKeys { get; set; } = new();
        public List<Fingerprint>? Fingerprints { get; set; } = new();
        public List<PinCode>? PinCodes { get; set; } = new();
        public List<AccessLog>? AccessLogs { get; set; } = new();
        public DateTime CreatedAt { get; set; } = DateTimeHelper.GetUtcTime();
        public DateTime LastBatteryCheck { get; set; }
        public DateTime? UpdatedAt { get; set; }

    }
}
