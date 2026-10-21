#include "LoopDoor.h"
#include "LoopManager.h"
#include "EngineUtils.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"

ALoopDoor::ALoopDoor()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = false; // ticks only while swinging

	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	Hinge = CreateDefaultSubobject<USceneComponent>(TEXT("Hinge"));
	Hinge->SetupAttachment(RootComponent);

	// Greybox panel 100 x 5 x 205 cm; swap the mesh in Details for the real door.
	Panel = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Panel"));
	Panel->SetupAttachment(Hinge);
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
	Panel->SetStaticMesh(Cube.Object);
	Panel->SetRelativeLocation(FVector(0.f, 50.f, 102.5f));
	Panel->SetRelativeScale3D(FVector(0.05f, 1.f, 2.05f));
}

void ALoopDoor::BeginPlay()
{
	Super::BeginPlay();

	if (TActorIterator<ALoopManager> It(GetWorld()); It)
	{
		It->OnStageStarted.AddDynamic(this, &ALoopDoor::OnStageStarted);
		It->OnStageRepeated.AddDynamic(this, &ALoopDoor::OnStageRepeated);
	}
}

void ALoopDoor::Interact_Implementation(AActor* Caller)
{
	SetOpen(TargetYaw == 0.f);
}

void ALoopDoor::SetOpen(bool bOpen, bool bInstant)
{
	TargetYaw = bOpen ? OpenAngle : 0.f;
	if (bInstant)
	{
		Hinge->SetRelativeRotation(FRotator(0.f, TargetYaw, 0.f));
	}
	SetActorTickEnabled(!bInstant);
}

void ALoopDoor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	const float Yaw = FMath::FInterpConstantTo(Hinge->GetRelativeRotation().Yaw, TargetYaw, DeltaSeconds, OpenSpeed);
	Hinge->SetRelativeRotation(FRotator(0.f, Yaw, 0.f));
	if (FMath::IsNearlyEqual(Yaw, TargetYaw))
	{
		SetActorTickEnabled(false);
	}
}

void ALoopDoor::OnStageStarted(int32 Stage)
{
	SetOpen(false, true);
}

void ALoopDoor::OnStageRepeated(int32 Stage, int32 RepeatCount)
{
	SetOpen(false, true);
}
