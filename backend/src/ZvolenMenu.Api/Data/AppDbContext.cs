using Microsoft.EntityFrameworkCore;
using ZvolenMenu.Api.Models;

namespace ZvolenMenu.Api.Data;

public class AppDbContext(DbContextOptions<AppDbContext> options) : DbContext(options)
{
    public DbSet<Restaurant> Restaurants => Set<Restaurant>();
    public DbSet<DailyMenu> DailyMenus => Set<DailyMenu>();
    public DbSet<Meal> Meals => Set<Meal>();
    public DbSet<MenuType> MenuTypes => Set<MenuType>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Restaurant>(entity =>
        {
            entity.ToTable("Restaurants");
            entity.Property(r => r.Name).HasMaxLength(200).IsRequired();
            entity.Property(r => r.Address).HasMaxLength(300).IsRequired();
            entity.Property(r => r.Phone).HasMaxLength(40);
            entity.Property(r => r.Website).HasMaxLength(300);
        });

        modelBuilder.Entity<DailyMenu>(entity =>
        {
            entity.ToTable("DailyMenus");
            entity.HasIndex(m => new { m.RestaurantId, m.MenuDate }).IsUnique();
            entity.Property(m => m.Note).HasMaxLength(500);
            entity.HasOne(m => m.Restaurant)
                .WithMany(r => r.DailyMenus)
                .HasForeignKey(m => m.RestaurantId)
                .OnDelete(DeleteBehavior.Cascade);
        });

        modelBuilder.Entity<Meal>(entity =>
        {
            entity.ToTable("Meals");
            entity.Property(i => i.Name).HasMaxLength(300).IsRequired();
            entity.Property(i => i.Description).HasMaxLength(500);
            entity.Property(i => i.Allergens).HasMaxLength(200);
            entity.Property(i => i.Price).HasPrecision(8, 2);
            entity.HasOne(i => i.DailyMenu)
                .WithMany(m => m.Items)
                .HasForeignKey(i => i.DailyMenuId)
                .OnDelete(DeleteBehavior.Cascade);
            entity.HasOne(i => i.MenuType)
                .WithMany(t => t.Meals)
                .HasForeignKey(i => i.MenuTypeId)
                .OnDelete(DeleteBehavior.Restrict);
        });

        modelBuilder.Entity<MenuType>(entity =>
        {
            entity.ToTable("MenuTypes");
            entity.Property(t => t.Name).HasMaxLength(80).IsRequired();
            entity.HasIndex(t => t.Name).IsUnique();
        });
    }
}
