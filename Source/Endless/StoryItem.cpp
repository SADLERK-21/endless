#include "StoryItem.h"
#include "Endless.h"
#include "LoopManager.h"
#include "EngineUtils.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/GameViewportClient.h"
#include "Engine/StaticMesh.h"
#include "Styling/CoreStyle.h"
#include "TimerManager.h"
#include "UObject/ConstructorHelpers.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"

AStoryItem::AStoryItem()
{
	// Separate root: the 0.2 scale lives on the mesh, so placing the actor with scale 1 keeps it small
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	Mesh->SetupAttachment(RootComponent);
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
	Mesh->SetStaticMesh(Cube.Object);
	Mesh->SetRelativeScale3D(FVector(0.2f));
}

void AStoryItem::BeginPlay()
{
	Super::BeginPlay();

	TActorIterator<ALoopManager> It(GetWorld());
	Manager = It ? *It : nullptr;
	if (!Manager)
	{
		UE_LOG(LogEndless, Error, TEXT("%s: no LoopManager in level"), *GetActorNameOrLabel());
	}
}

void AStoryItem::Interact_Implementation(AActor* Caller)
{
	if (!Manager || bUsed)
	{
		return;
	}
	bUsed = true;
	Manager->CompleteObjective();
	UE_LOG(LogEndless, Log, TEXT("%s used: stage %d objective done"), *GetActorNameOrLabel(), Manager->CurrentStage);
	if (bHideOnUse)
	{
		SetActorHiddenInGame(true);
		SetActorEnableCollision(false);
	}
	if (!UseMessage.IsEmpty())
	{
		ShowSubtitle();
	}
	OnUsed();
}

void AStoryItem::ShowSubtitle()
{
	UGameViewportClient* Viewport = GetWorld()->GetGameViewport();
	if (!Viewport)
	{
		return;
	}
	// shortcut: a Slate line stands in for the voiced / scripted story moment until real UI and audio (MVP week 5)
	const TSharedRef<SWidget> Line = SNew(SBox)
		.HAlign(HAlign_Center)
		.VAlign(VAlign_Bottom)
		.Padding(FMargin(120.f, 0.f, 120.f, 90.f))
		[
			SNew(STextBlock)
			.Text(UseMessage)
			.AutoWrapText(true)
			.Justification(ETextJustify::Center)
			.Font(FCoreStyle::GetDefaultFontStyle("Regular", 22))
			.ShadowOffset(FVector2D(1.f, 1.f))
		];
	Viewport->AddViewportWidgetContent(Line);

	const TWeakPtr<SWidget> WeakLine = Line;
	const TWeakObjectPtr<UGameViewportClient> WeakViewport = Viewport;
	FTimerHandle Timer;
	GetWorldTimerManager().SetTimer(Timer, FTimerDelegate::CreateLambda([WeakLine, WeakViewport]
	{
		if (WeakViewport.IsValid() && WeakLine.IsValid())
		{
			WeakViewport->RemoveViewportWidgetContent(WeakLine.Pin().ToSharedRef());
		}
	}), SubtitleSeconds, false);
}
