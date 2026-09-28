using Microsoft.EntityFrameworkCore;
using ZvolenMenu.Api.Data;

var builder = WebApplication.CreateBuilder(args);

var dataDir = Path.GetFullPath(Path.Combine(builder.Environment.ContentRootPath, "..", "..", "data"));
Directory.CreateDirectory(dataDir);
var dbPath = Path.Combine(dataDir, "zvolenmenu.db");

builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlite($"Data Source={dbPath}"));

builder.Services.AddControllers();
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
        policy.WithOrigins("http://localhost:5173")
            .AllowAnyHeader()
            .AllowAnyMethod());
});

var app = builder.Build();

using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    // Ensure database file exists and create EF model tables when possible
    await db.Database.EnsureCreatedAsync();

    // If some tables are missing (existing DB), create them individually
    await EnsureTablesExistAsync(db);

    await SeedData.EnsureSeededAsync(db);
}

// Local helper: check sqlite_master and create any missing tables/indexes
static async Task EnsureTablesExistAsync(ZvolenMenu.Api.Data.AppDbContext db)
{
    var required = new Dictionary<string, string>
    {
        ["Restaurants"] = @"CREATE TABLE IF NOT EXISTS ""Restaurants"" (
            ""Id"" INTEGER NOT NULL CONSTRAINT ""PK_Restaurants"" PRIMARY KEY AUTOINCREMENT,
            ""Name"" TEXT NOT NULL,
            ""Address"" TEXT NOT NULL,
            ""Latitude"" REAL NOT NULL,
            ""Longitude"" REAL NOT NULL,
            ""Phone"" TEXT NULL,
            ""Website"" TEXT NULL
        );",

        ["MenuTypes"] = @"CREATE TABLE IF NOT EXISTS ""MenuTypes"" (
            ""Id"" INTEGER NOT NULL CONSTRAINT ""PK_MenuTypes"" PRIMARY KEY AUTOINCREMENT,
            ""Name"" TEXT NOT NULL
        );",

        ["DailyMenus"] = @"CREATE TABLE IF NOT EXISTS ""DailyMenus"" (
            ""Id"" INTEGER NOT NULL CONSTRAINT ""PK_DailyMenus"" PRIMARY KEY AUTOINCREMENT,
            ""RestaurantId"" INTEGER NOT NULL,
            ""MenuDate"" TEXT NOT NULL,
            ""Note"" TEXT NULL,
            CONSTRAINT ""FK_DailyMenus_Restaurants_RestaurantId"" FOREIGN KEY (""RestaurantId"") REFERENCES ""Restaurants"" (""Id"") ON DELETE CASCADE
        );",

        ["Meals"] = @"CREATE TABLE IF NOT EXISTS ""Meals"" (
            ""Id"" INTEGER NOT NULL CONSTRAINT ""PK_Meals"" PRIMARY KEY AUTOINCREMENT,
            ""DailyMenuId"" INTEGER NOT NULL,
            ""MenuTypeId"" INTEGER NOT NULL,
            ""Name"" TEXT NOT NULL,
            ""Description"" TEXT NULL,
            ""Allergens"" TEXT NULL,
            ""Price"" TEXT NOT NULL,
            ""SortOrder"" INTEGER NOT NULL,
            CONSTRAINT ""FK_Meals_DailyMenus_DailyMenuId"" FOREIGN KEY (""DailyMenuId"") REFERENCES ""DailyMenus"" (""Id"") ON DELETE CASCADE,
            CONSTRAINT ""FK_Meals_MenuTypes_MenuTypeId"" FOREIGN KEY (""MenuTypeId"") REFERENCES ""MenuTypes"" (""Id"") ON DELETE RESTRICT
        );"
    };

    var indexSql = new[]
    {
        "CREATE UNIQUE INDEX IF NOT EXISTS \"IX_DailyMenus_RestaurantId_MenuDate\" ON \"DailyMenus\" (\"RestaurantId\", \"MenuDate\");",
        "CREATE INDEX IF NOT EXISTS \"IX_Meals_DailyMenuId\" ON \"Meals\" (\"DailyMenuId\");",
        "CREATE UNIQUE INDEX IF NOT EXISTS \"IX_MenuTypes_Name\" ON \"MenuTypes\" (\"Name\");"
    };

    var conn = db.Database.GetDbConnection();
    try
    {
        await conn.OpenAsync();
        foreach (var kv in required)
        {
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT name FROM sqlite_master WHERE type='table' AND name=@name;";
            var p = cmd.CreateParameter(); p.ParameterName = "@name"; p.Value = kv.Key; cmd.Parameters.Add(p);
            var exists = await cmd.ExecuteScalarAsync();
            if (exists is null)
            {
                using var create = conn.CreateCommand();
                create.CommandText = kv.Value;
                await create.ExecuteNonQueryAsync();
            }
        }

        foreach (var sql in indexSql)
        {
            using var c = conn.CreateCommand();
            c.CommandText = sql;
            await c.ExecuteNonQueryAsync();
        }
    }
    finally
    {
        await conn.CloseAsync();
    }
}

app.UseCors();
app.MapControllers();
app.Run();
