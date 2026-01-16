namespace Resido.Database.DBTable
{
    public class Fingerprint
    {
        public Guid Id { get; set; }

        // Corresponding int fingerprint ID from device
        public int FingerprintId { get; set; }

        public string FingerName { get; set; }

        public Guid SmartLockId { get; set; }
        public virtual SmartLock SmartLock { get; set; }

        public DateTime CreatedAt { get; set; }

        public DateTime? UpdatedAt { get; set; }
    }
}
