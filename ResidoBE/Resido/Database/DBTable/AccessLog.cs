using Resido.Helper;

namespace Resido.Database.DBTable
{
    public class AccessLog
    {
        public Guid Id { get; set; } = Guid.NewGuid();
        public int LockId { get; set; }
        public string? LockMac { get; set; }
        public int RecordType { get; set; }
        public int RecordTypeFromLock { get; set; }
        public string? RecordTypeDescription { get; set; }
        public string? Username { get; set; }
        public string? KeyboardPwd { get; set; }

        public int Success { get; set; }
        public Guid SmartLockId { get; set; }
        public virtual SmartLock SmartLock { get; set; } = null!;

        // Status & device info
        public int BatteryPercentage { get; set; }
        public bool IsAccessSuccessful { get; set; }

        // Time captured on lock (local time)
        public long LockEventLocalTime { get; set; }

        // Time captured on server (local time)
        public long ServerReceivedLocalTime { get; set; }

        // Time captured on lock (UTC)
        public DateTime LockEventUtcTime { get; set; }

        // Time captured on server (UTC)
        public DateTime ServerReceivedUtcTime { get; set; }

        // Audit
        public DateTime CreatedAt { get; set; } = DateTimeHelper.GetUtcTime();

    }
}
